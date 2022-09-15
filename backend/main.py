import uvicorn
from fastapi import FastAPI, status
import crud
import schemas
from db_manager import create_db, get_db
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta

create_db()  # generate tables if they don't exist

app = FastAPI()


######################################
# exceptions
######################################
class ItemNotFound(Exception):
    def __init__(self, name: str):
        self.name = name


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(schemas.Error(code=400, message="Validation Failed")),
    )


@app.exception_handler(ItemNotFound)
async def unicorn_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=jsonable_encoder(schemas.Error(code=404, message="Item not found")),
    )
######################################


def check_validity(db: Session, items: schemas.SystemItemImportRequest):
    """
    check validity of items
    :param db: db-session
    :param items: items for checking
    :return: result of checking
    """
    if items.items is None:
        return False
    import_files = dict()
    for item in items.items:
        if item.id in import_files:
            return False
        import_files[item.id] = item.type
        item_in_db = crud.get_item(db, item.id)
        if item_in_db:
            if item_in_db.type != item.type:
                return False

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


def update_folder_size(db: Session, folder_id: str, size_delta: int, date: datetime):
    """
    update size of folder and put it into history
    :param db: db session
    :param folder_id: id of folder
    :param size_delta: size delta
    :param date: date of request
    :return: list of updated folders
    """
    sql_folder = crud.get_item(db, folder_id)
    crud.update_folder_size(db, folder_id, sql_folder.size + size_delta, date)
    list_updated_folders = [folder_id]
    if sql_folder.parentId:
        list_updated_folders += update_folder_size(db, sql_folder.parentId, size_delta, date)
    return list_updated_folders


@app.post("/imports")
async def imports(items: schemas.SystemItemImportRequest):
    """
    API function for importing data
    :param items: items that should be added
    :return: code and message of result
    """
    db = get_db()
    # check for data validity
    if not check_validity(db, items):
        db.close()
        raise RequestValidationError("error")

    folders_size_delta = dict()
    new_folders = []

    # add each item into db
    for item in items.items:
        if item.type == schemas.SystemItemType.FOLDER:
            item.size = 0

        temp = crud.get_item(db, item.id)
        if temp:  # if object exist, then remove it for updating
            if item.type == schemas.SystemItemType.FOLDER:
                item.size = temp.size
            crud.delete_item(db, item.id)

        crud.add_item(db, item, items.updateDate)

        if item.type == schemas.SystemItemType.FILE:  # if it's folder we should update its size before put it into history
            crud.add_to_history(db, item, items.updateDate)
        else:
            new_folders.append(item.id)

        # check for update folders size
        if temp:
            if temp.parentId:
                if temp.parentId in folders_size_delta:
                    folders_size_delta[temp.parentId] = folders_size_delta[temp.parentId] - temp.size
                else:
                    folders_size_delta[temp.parentId] = -temp.size
        if item.parentId:
            if item.parentId in folders_size_delta:
                folders_size_delta[item.parentId] = folders_size_delta[item.parentId] + item.size
            else:
                folders_size_delta[item.parentId] = item.size

    updated_folders = set()
    updated_folders.update(new_folders)

    for folder_id in folders_size_delta:  # update folders size
        updated_folders.update(update_folder_size(db, folder_id, folders_size_delta[folder_id], items.updateDate))

    for folder_id in updated_folders:  # add to history folders updates
        sql_folder = crud.get_item(db, folder_id)
        folder_import = schemas.SystemItemImport(id=sql_folder.id, url=sql_folder.url, parentId=sql_folder.parentId,
                                                 type=sql_folder.type, size=sql_folder.size)
        crud.add_to_history(db, folder_import, items.updateDate)

    db.close()
    return JSONResponse(content=jsonable_encoder(schemas.Error(code=200, message="The insert or update was successful")))


@app.delete("/delete/{id}")
async def delete(id: str, date: datetime):
    """
    API function for deleting data
    :param id: id of object
    :param date: date of the request
    :return: code and message of result
    """
    db = get_db()
    item = crud.get_item(db, id)
    if item:  # check for existing of object
        if item.type == schemas.SystemItemType.FOLDER:  # remove also children
            delete_children(db, id)
        crud.delete_item(db, id)
        crud.remove_from_history(db, id)
        updated_folders = []
        if item.parentId:
            updated_folders += update_folder_size(db, item.parentId, -item.size, date)

        for folder_id in updated_folders:  # add to history folders updates
            sql_folder = crud.get_item(db, folder_id)
            folder_import = schemas.SystemItemImport(id=sql_folder.id, url=sql_folder.url, parentId=sql_folder.parentId,
                                                     type=sql_folder.type, size=sql_folder.size)
            crud.add_to_history(db, folder_import, date)

        db.close()
        return JSONResponse(content=jsonable_encoder(schemas.Error(code=200, message="Removal was successful")))
    else:
        db.close()
        raise ItemNotFound("error")


def delete_children(db: Session, id: str):
    """
    remove children of object if they exist
    :param db: db session
    :param id: if of object
    """
    children = crud.search_children(db, id)
    for child in children:
        if child.type == schemas.SystemItemType.FOLDER:  # check children of child
            delete_children(db, child.id)
        crud.delete_item(db, child.id)
        crud.remove_from_history(db, id)


@app.get("/nodes/{id}")
async def get_node(id: str):
    """
    API function for returning data of object
    :param id: id of object
    :return: code and message of result
    """
    db = get_db()
    sql_item = crud.get_item(db, id)
    if sql_item:  # check for existing of object
        fix_date = sql_item.date.isoformat() + "Z"
        sys_item = schemas.SystemItem(id=sql_item.id, url=sql_item.url, date=fix_date,
                                      parentId=sql_item.parentId, type=sql_item.type, size=sql_item.size)
        json_item = jsonable_encoder(sys_item)

        if sys_item.type == schemas.SystemItemType.FOLDER:
            if sys_item.size != 0:
                json_item['children'] = get_children(db, id)  # get data of children and compile response
            else:
                json_item['children'] = []
        else:
            json_item['children'] = None

        db.close()
        return JSONResponse(content=json_item)
    else:
        db.close()
        raise ItemNotFound("error")


@app.get("/updates")
async def get_updates(date: datetime):
    """
    API function for returning data of updates of files
    :param date: start date of update
    :return: code and message of result
    """
    db = get_db()
    sql_items = crud.get_updates(db, date - timedelta(days=1))
    db.close()

    json_items = []
    for sql_item in sql_items:  # compile response
        fix_date = sql_item.date.isoformat() + "Z"
        history_item = schemas.SystemItemHistoryUnit(id=sql_item.id, url=sql_item.url, date=fix_date,
                                      parentId=sql_item.parentId, type=sql_item.type, size=sql_item.size)
        json_items.append(jsonable_encoder(history_item))

    return JSONResponse(content=json_items)


@app.get("/node/{id}/history")
async def get_history(id: str, dateStart: datetime = None, dateEnd: datetime = None):
    """
    API function for returning data of history of object in time range
    :param id: id of object
    :param dateStart: start date
    :param dateEnd: end date
    :return: code and message of result
    """
    db = get_db()
    item = crud.get_item(db, id)
    if item:  # check for object existing
        history = []
        # select suitable function according input data
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

        for sql_history_item in sql_history:  # compile response
            fix_date = sql_history_item.date.isoformat() + "Z"
            history.append(schemas.SystemItemHistoryUnit(id=sql_history_item.id, url=sql_history_item.url,
                                                         date=fix_date, parentId=sql_history_item.parentId,
                                                         type=sql_history_item.type, size=sql_history_item.size))

        history_response = schemas.SystemItemHistoryResponse(items=history)
        return JSONResponse(content=jsonable_encoder(history_response))
    else:
        raise ItemNotFound("error")


def get_children(db: Session, id: str):
    """
    search children of object
    :param db: db session
    :param id: id of object
    :return: data of children
    """
    sql_children = crud.search_children(db, id)
    if sql_children:  # check for children existing
        json_children = []
        for sql_child in sql_children:
            fix_date = sql_child.date.isoformat() + "Z"
            sys_child = schemas.SystemItem(id=sql_child.id, url=sql_child.url, date=fix_date,
                                           parentId=sql_child.parentId, type=sql_child.type, size=sql_child.size)
            json_child = jsonable_encoder(sys_child)

            if sys_child.type == schemas.SystemItemType.FOLDER:
                if sys_child.size != 0:
                    # get data of children of child
                    json_child['children'] = get_children(db, sys_child.id)
                else:
                    json_child['children'] = []
            else:
                json_child['children'] = None

            json_children.append(json_child)
        return json_children
    else:
        return []


# start server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
