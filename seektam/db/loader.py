#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import argparse
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.scoping import scoped_session
from . import koreafood
from . import model

# logging
formatter = logging.Formatter('%(asctime)-15s [%(levelname)s] '
                              '%(threadName)s.%(funcName)s: %(message)s')
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)


def food_to_model(sess, food):
    ret = []
    mfood = model.Food()
    mfood.name = food.name
    mfood.category_big = food.category_big
    mfood.category_small = food.category_small

    for k in food.aliment:
        try:
            maliment = sess.query(model.Aliment).filter(
                model.Aliment.name == k).one()
        except NoResultFound:
            arr = food.aliment[k]
            maliment = model.Aliment()
            columns = [
                'weight', 'energy', 'moisture', 'protein', 'fat',
                'nonfiborous', 'fiber', 'ash', 'calcium', 'potassium',
                'retinol_equivalent', 'retinol', 'betacarotene',
                'thiamin', 'riboflavin', 'niacin', 'ascobic_acid'
                ]

            maliment.name = k
            weight = float(arr[0].replace(',', '')) or 1.0
            for c in columns[1:]:
                setattr(maliment, c, float(arr[columns.index(c)]) / weight)
        finally:
            ret.append(maliment)

    mfood.aliments = ret
    return mfood


def add_model(session, model, filter_func, instance):
    try:
        item = session.query(model).filter(filter_func).all()
        if item == []:
            raise NoResultFound
        logger.debug(
            u'{} {} is already in database'.format(
                model.__name__, instance.name))
        return False
    except NoResultFound:
        pass

    logger.info(u'{} {} added'.format(model.__name__, instance.name))
    session.add(instance)
    session.commit()
    return True


def add_food_aliment(session, mfood, maliment):
    f = session.query(model.Food).filter(
        model.Food.name == mfood.name).one()
    a = session.query(model.Aliment).filter(
        model.Aliment.name == maliment.name).one()

    rel = model.FoodAlimentRelation()
    rel.food_id = f.id
    rel.aliment_id = a.id
    session.add(rel)
    try:
        session.commit()
        logger.info(u'Food {} <-> Aliment {} added'.format(f.name, a.name))
    except:
        logger.error('Food-Aliment relation set failed')


def add_food(session, mfood):
    return add_model(
        session, model.Food, model.Food.name == mfood.name, mfood)


def add_aliment(session, maliment):
    return add_model(
        session, model.Aliment, model.Aliment.name == maliment.name, maliment)


def loader(url):
    engine = create_engine(url)
    Session = scoped_session(sessionmaker(engine))
    sess = Session()

    model.Base.metadata.bind = engine
    model.Base.metadata.create_all()

    for food in koreafood.get_food_list():
        mfood = food_to_model(sess, food)
        add_food(sess, mfood)
        for aliment in mfood.aliments:
            add_aliment(sess, aliment)
            add_food_aliment(sess, mfood, aliment)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'url',
        help='Database URL (ex. mysql://scott@tiger:example.com/dbname)'
        )
    args = parser.parse_args()

    if not args.url:
        logger.error('Missing database url')
        return

    return loader(args.url)


if __name__ == '__main__':
    main()
