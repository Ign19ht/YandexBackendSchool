import uvicorn
from fastapi import FastAPI
import crud
import schemas
from db_manager import create_db, get_db
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import UnmappedInstanceError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timedelta

create_db()

app = FastAPI()


def check_validity(db: Session, items: schemas.SystemItemImportRequest):
    import_files = dict()
    for item in items.items:
        if item.id in import_files:
            return False
        import_files[item.id] = item.type

    for item in items.items:
        if item.parentId is not None:
            parent = crud.get_item(db, item.parentId)
            if parent:
                if parent.type != schemas.SystemItemType.FOLDER:
                    return False
            else:
                if item.parentId not in import_files or import_files[item.parentId] != schemas.SystemItemType.FOLDER:
                    return False
        if item.type == schemas.SystemItemType.FOLDER:
            if item.url is not None or item.size is not None:
                return False
        else:
            if item.url is not None and len(item.url) > 255:
                return False
            if item.size is None or item.size <= 0:
                return False

    return True


@app.exception_handler(RequestValidationError)
async def http_exception_handler(request, exc):
    return JSONResponse(content=jsonable_encoder(schemas.Error(code=400, message="Validation Failed")))


@app.post("/imports")
async def imports(items: schemas.SystemItemImportRequest):
    db = get_db()
    if not check_validity(db, items):
        db.close()
        raise RequestValidationError("error")

    for item in items.items:
        temp = crud.get_item(db, item.id)
        if temp:
            crud.delete_item(db, item.id)
        crud.add_item(db, item, items.updateDate)
    db.close()
    return JSONResponse(content=jsonable_encoder(schemas.Error(code=200, message="The insert or update was successful")))


@app.delete("/delete/{id}")
async def delete(id: str, date: str):
    db = get_db()
    try:
        crud.delete_item(db, id)
        crud.remove_from_history(db, id)
    except UnmappedInstanceError:
        db.close()
        return JSONResponse(content=jsonable_encoder(schemas.Error(code=404, message="Item not found")))
    db.close()
    return JSONResponse(content=jsonable_encoder(schemas.Error(code=200, message="Removal was successful")))


@app.get("/nodes/{id}")
async def get_node(id: str):
    db = get_db()
    sql_item = crud.get_item(db, id)
    if sql_item:
        print(sql_item.parentId)
        sys_item = schemas.SystemItem(id=sql_item.id, url=sql_item.url, date=sql_item.date,
                                      parentId=sql_item.parentId, type=sql_item.type, size=sql_item.size)
        json_item = jsonable_encoder(sys_item)

        children = get_children(db, id)
        if children:
            json_item['children'] = children
        else:
            json_item.pop("children", None)

        db.close()
        return JSONResponse(content=json_item)
    else:
        db.close()
        return JSONResponse(content=jsonable_encoder(schemas.Error(code=404, message="Item not found")))


@app.get("/updates")
async def get_updates(date: datetime):
    db = get_db()
    sql_items = crud.get_updates(db, date - timedelta(days=1))
    db.close()

    json_items = []
    for sql_item in sql_items:
        history_item = schemas.SystemItemHistoryUnit(id=sql_item.id, url=sql_item.url, date=sql_item.date,
                                      parentId=sql_item.parentId, type=sql_item.type, size=sql_item.size)
        json_items.append(jsonable_encoder(history_item))

    return JSONResponse(content=json_items)


@app.get("/node/{id}/history")
async def get_history(id: str, dateStart: datetime = None, dateEnd: datetime = None):
    db = get_db()
    item = crud.get_item(db, id)
    if item:
        history = []
        if dateEnd is None:
            if dateStart is None:
                sql_history = crud.get_all_history(db, id)
            else:
                sql_history = crud.get_history_from(db, id, dateStart)
        else:
            if dateStart is None:
                sql_history = crud.get_history_to(db, id, dateEnd)
            else:
                sql_history = crud.get_history(db, id, dateStart, dateEnd)
        db.close()
        for sql_history_item in sql_history:
            history.append(schemas.SystemItemHistoryUnit(id=sql_history_item.id, url=sql_history_item.url,
                                                         date=sql_history_item.date, parentId=sql_history_item.parentId,
                                                         type=sql_history_item.type, size=sql_history_item.size))
        history_response = schemas.SystemItemHistoryResponse(items=history)
        return JSONResponse(content=jsonable_encoder(history_response))
    else:
        return JSONResponse(content=jsonable_encoder(schemas.Error(code=404, message="Item not found")))


def get_children(db: Session, id: str):
    sql_children = crud.search_children(db, id)
    if sql_children:
        json_children = []
        for sql_child in sql_children:
            sys_child = schemas.SystemItem(id=sql_child.id, url=sql_child.url, date=sql_child.date,
                                           parentId=sql_child.parentId, type=sql_child.type, size=sql_child.size)
            json_child = jsonable_encoder(sys_child)

            children_of_child = get_children(db, sys_child.id)
            if children_of_child:
                json_child['children'] = children_of_child
            else:
                json_child.pop("children", None)

            json_children.append(json_child)
        return json_children
    else:
        return None


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
