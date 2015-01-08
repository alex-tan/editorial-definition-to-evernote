# -*- coding: utf-8 -*-


# Gets an xml node. If it is a text node, returns the text, otherwise
# it joins the text of all its child nodes.
def extract_node_text(node):
    if hasattr(node, 'data'):
        return node.data
    else:
        strings = map(extract_node_text, node.childNodes)
        return "".join(strings)


# Takes a definition string and replaces the colon with '- '
# so that it will appear as part of a markdown list.
def format_definition(definition):
    nodes = map(extract_node_text, definition.childNodes)
    return re.sub(r'^:', '- ', "".join(nodes))


# Takes an array of notebooks and finds the guid of the specified
# notebook name.
def find_notebook_guid(notebooks, notebook_name):
    for index, notebook in enumerate(notebooks):
        if notebook.name == notebook_name:
            return notebook.guid


def get_token(keychain_name, password_name):
    login = keychain.get_password(keychain_name, 'editorial')
    if login is not None:
        return pickle.loads(login)
    else:
        token_choice = console.alert('Token Needed', 'A ' + password_name + ' is needed. Do you have one?', 'Yes')
        if token_choice == 1:
            auth_token = console.password_alert(password_name, 'Paste Your ' + password_name)
            pickle_token = pickle.dumps(auth_token)
            keychain.set_password(keychain_name, 'editorial', pickle_token)
            return auth_token
        else:
            raise KeyboardInterrupt

import pickle
import keychain
import workflow
import console
import urllib2
import xml.sax
import re
import xml.dom.minidom

import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient

# Configure
word = workflow.get_input()
dictionary_api_key = get_token('dictionary_api', 'dictionaryapi.com API Token')
evernote_auth_token = get_token('evernote_api', 'Evernote API Token')
evernote_notebook_name = 'Words'

# Put together the API url
api_url = 'http://www.dictionaryapi.com/api/v1/references/collegiate/xml/' + word + '?key=' + dictionary_api_key

# Make the API request
handler = urllib2.urlopen(api_url)
contents = handler.read()

# Open XML document
document = xml.dom.minidom.parseString(contents).documentElement

# Get all the definitions.
definitions = map(format_definition, document.getElementsByTagName("dt"))

note_content = "<br/>".join(definitions)

# Initialize Evernote Client
client = EvernoteClient(token=evernote_auth_token, sandbox=False)
note_store = client.get_note_store()

# Create the note
note = Types.Note()
note.title = word
note.notebookGuid = find_notebook_guid(note_store.listNotebooks(), evernote_notebook_name)

note.content = '<?xml version="1.0" encoding="UTF-8"?>'
note.content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
note.content += '<en-note>'
note.content += note_content
note.content += '</en-note>'

# Finally, send the new note to Evernote using the createNote method
# The new Note object that is returned will contain server-generated
# attributes such as the new note's unique GUID.
note_store.createNote(note)

console.hud_alert("'" + word + "' definition added to Evernote notebook " + evernote_notebook_name, 'success')

# Return the word to Editorial
workflow.set_output(word)
