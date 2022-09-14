from typing import List

from sqlalchemy.orm import Session
import models
import schemas
from datetime import datetime


def add_item(db: Session, item: schemas.SystemItemImport, date: datetime):
    """
    add item into items and history tables
    :param db: db session
    :param item: item that should be added
    :param date: date of request
    """
    db_item = models.Items(id=item.id, url=item.url, parentId=item.parentId, size=item.size,
                           type=item.type, date=date)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)


def delete_item(db: Session, id: str):
    """
    delete item from items table
    :param db: db session
    :param id: id of object
    """
    db.delete(db.query(models.Items).filter(models.Items.id == id).first())
    db.commit()


def get_item(db: Session, id: str) -> models.Items:
    """
    get data of item from items table
    :param db: db session
    :param id: id of object
    :return: data of item
    """
    return db.query(models.Items).filter(models.Items.id == id).first()


def search_children(db: Session, parent_id: str) -> List[models.Items]:
    """
    search children of object in items table
    :param db: db session
    :param parent_id: id of parent
    :return: data of children of object
    """
    return db.query(models.Items).filter(models.Items.parentId == parent_id).all()


def get_updates(db: Session, date: datetime):
    """
    search data of updates of object since date in items table
    :param db: db session
    :param date: start date
    :return: data of updates
    """
    return db.query(models.Items).filter(models.Items.date >= date).all()


def update_folder_size(db: Session, id: str):
    """
    update size of folder
    :param db: db session
    :param id: id of file
    """
    children = search_children(db, id)
    db.query(models.Items).filter(models.Items.id == id).update({"size": len(children)})
    db.commit()


def add_to_history(db: Session, item: schemas.SystemItemImport, date: datetime):
    """
    add note into history
    :param db: db session
    :param item: item
    :param date: date of request
    """
    db_history = models.History(id=item.id, url=item.url, parentId=item.parentId, size=item.size,
                                type=item.type, date=date)
    db.add(db_history)
    db.commit()
    db.refresh(db_history)


def remove_from_history(db: Session, id: str):
    """
    remove history of object from history table
    :param db: db session
    :param id: id of object
    """
    history_all = db.query(models.History).filter(models.History.id == id).all()
    for history in history_all:
        db.delete(history)
    db.commit()


def get_history(db: Session, id: str, date_start: datetime, date_end: datetime):
    """
    search history of object in time range in history table
    :param db: db session
    :param id: id of object
    :param date_start: start date
    :param date_end: end date
    :return: history of object
    """
    return db.query(models.History)\
        .filter(models.History.id == id)\
        .filter(date_end >= models.History.date)\
        .filter(models.History.date >= date_start).all()


def get_history_from(db: Session, id: str, date_start: datetime):
    """
    search history of object after input date in history table
    :param db: db session
    :param id: id of object
    :param date_start: start date
    :return: history of object
    """
    return db.query(models.History)\
        .filter(models.History.id == id).filter(models.History.date >= date_start).all()


def get_history_to(db: Session, id: str, date_end: datetime):
    """
    search history of object before input date in history table
    :param db: db session
    :param id: id of object
    :param date_end: end date
    :return: history of object
    """
    return db.query(models.History)\
        .filter(models.History.id == id).filter(models.History.date <= date_end).all()


def get_all_history(db: Session, id: str):
    """
    search all history of object in history table
    :param db: db session
    :param id: id of object
    :return: history of object
    """
    return db.query(models.History).filter(models.History.id == id).all()
