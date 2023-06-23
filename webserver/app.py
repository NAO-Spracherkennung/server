#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import spacy
from flask import request, jsonify, Flask
from db_util import getDbConnection

import counter
import db_connector
import sentence_algorithm
import requests

TRANSCRIBER_HOST = os.environ["TRANSCRIBER_HOST"]
TRANSCRIBER_PORT = os.environ["TRANSCRIBER_PORT"]

app = Flask(__name__)

cursor = getDbConnection()


@app.route('/', methods=['GET'])
def get_request():
    question = request.args.get('question')
    if question is None or len(question) < 1:
        return jsonify("This is the server of nao.")
    nlp = spacy.load("de_core_news_sm")
    doc = nlp(question)
    found_words = sentence_algorithm.sentence_detection(doc)
    i = 0
    while i < len(found_words):
        found_words[i] = found_words[i].lower()
        wd = db_connector.get_generic_term(found_words[i], cursor)
        if wd is None:
            i += 1
            continue
        found_words[i] = wd
        i += 1
    caseID = counter.count_ids(found_words, cursor)
    if caseID is None:
        return jsonify("Ich habe diese Frage nicht verstanden oder ich habe dazu leider keine Antwort.")
    answer = db_connector.get_answer(caseID, cursor)
    if answer is None:
        return jsonify("-1")
    return answer


@app.route('/', methods=['POST'])
def post_request():

    url = 'http://'+TRANSCRIBER_HOST+':'+TRANSCRIBER_PORT+'/'
    files = {'file': request.files['file']}
    question = requests.post(url, files=files).text

    if question is None or len(question) < 1:
        return jsonify("This is the server of nao.")
    
    nlp = spacy.load("de_core_news_sm")
    doc = nlp(question)
    found_words = sentence_algorithm.sentence_detection(doc)
    i = 0
    while i < len(found_words):
        found_words[i] = found_words[i].lower()
        wd = db_connector.get_generic_term(found_words[i], cursor)
        if wd is None:
            i += 1
            continue
        found_words[i] = wd
        i += 1
    caseID = counter.count_ids(found_words, cursor)
    if caseID is None:
        print("nicht verstanden")
        return jsonify("Ich habe diese Frage nicht verstanden oder ich habe dazu leider keine Antwort.")
    answer = db_connector.get_answer(caseID, cursor)
    if answer is None:
        print("-1")
        return jsonify("-1")
    print(answer)
    return answer


@app.route('/answers', methods=['GET', 'POST'])
def answers():
    if request.method == 'POST':
        case_id = request.form.get('caseID')
        keywords = request.form.get('keywords')
        answer = request.form.get('answer')
        db_connector.insert_answers(case_id, keywords, answer, cur=cursor)
        return 'OK'
    else:
        return db_connector.get_all_answers(cursor)


@app.route('/genericTerms', methods=['GET', 'POST'])
def generic_terms():
    if request.method == 'POST':
        gn_id = request.form.get('id')
        generic_term = request.form.get('generic_term')
        db_connector.insert_generic_terms(gn_id, generic_term, cursor)
        return 'OK'
    else:
        return db_connector.get_all_generic_terms(cursor)


@app.route('/synonyms', methods=['GET', 'POST'])
def synonyms():
    if request.method == 'POST':
        synonym = request.form.get('synonym')
        syn_id = request.form.get('id')
        db_connector.insert_synonyms(synonym, syn_id, cursor)
        return 'OK'
    else:
        return db_connector.get_all_synonyms(cursor)


@app.route('/weights', methods=['GET'])
def weights():
    return db_connector.get_weights(cursor)