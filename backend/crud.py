from typing import List

from sqlalchemy.orm import Session
import models
import schemas
from datetime import datetime


def add_item(db: Session, item: schemas.SystemItemImport, date: datetime):
    db_item = models.Items(id=item.id, url=item.url, parentId=item.parentId, size=item.size,
                           type=item.type, date=date)
    db_history = models.History(id=item.id, url=item.url, parentId=item.parentId, size=item.size,
                           type=item.type, date=date)
    db.add(db_item)
    db.add(db_history)
    db.commit()
    db.refresh(db_item)
    db.refresh(db_history)


def delete_item(db: Session, id: str):
    db.delete(db.query(models.Items).filter(models.Items.id == id).first())
    db.commit()


def get_item(db: Session, id: str) -> models.Items:
    return db.query(models.Items).filter(models.Items.id == id).first()


def search_children(db: Session, parent_id: str) -> List[models.Items]:
    return db.query(models.Items).filter(models.Items.parentId == parent_id).all()


def get_updates(db: Session, date: datetime):
    return db.query(models.Items).filter(models.Items.date >= date).all()


def remove_from_history(db: Session, id: str):
    db.delete(db.query(models.History).filter(models.History.id == id).all())
    db.commit()


def get_history(db: Session, id: str, date_start: datetime, date_end: datetime):
    return db.query(models.History)\
        .filter(models.History.id == id)\
        .filter(date_end >= models.History.date)\
        .filter(models.History.date >= date_start).all()


def get_history_from(db: Session, id: str, date_start: datetime):
    return db.query(models.History)\
        .filter(models.History.id == id).filter(models.History.date >= date_start).all()


def get_history_to(db: Session, id: str, date_end: datetime):
    return db.query(models.History)\
        .filter(models.History.id == id).filter(models.History.date <= date_end).all()


def get_all_history(db: Session, id: str):
    return db.query(models.History).filter(models.History.id == id).all()
