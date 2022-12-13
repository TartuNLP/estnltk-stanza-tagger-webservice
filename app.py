import logging
from flask import request, abort
from flask_cors import CORS

from nauron import Nauron

import settings

logger = logging.getLogger("gunicorn.error")

# Define application
app = Nauron(__name__, timeout=settings.MESSAGE_TIMEOUT, mq_parameters=settings.MQ_PARAMS)
CORS(app)

stanza = app.add_service(name=settings.SERVICE_NAME, remote=settings.DISTRIBUTED)
stanza_ensemble = app.add_service(name="ensemble" + settings.SERVICE_NAME, remote=settings.DISTRIBUTED)

if not settings.DISTRIBUTED:
    from stanza_tagger_worker import StanzaSyntaxTaggerWorker
    from ensemble_tagger_worker import StanzaSyntaxEnsembleTaggerWorker

    stanza.add_worker(StanzaSyntaxTaggerWorker())
    stanza_ensemble.add_worker(StanzaSyntaxEnsembleTaggerWorker())


#
# Endpoints for StanzaSyntaxTaggerWorker
#

@app.post('/estnltk/tagger/stanza_syntax')
def tagger_stanza_syntax():
    if request.content_length > settings.MAX_CONTENT_LENGTH:
        abort(413)
    response = stanza.process_request(content=request.json)
    return response


@app.get('/estnltk/tagger/stanza_syntax/about')
def tagger_stanza_syntax_about():
    return 'Tags dependency syntactic analysis using EstNLTK StanzaSyntaxTagger\'s webservice.'


@app.get('/estnltk/tagger/stanza_syntax/status')
def tagger_stanza_syntax_status():
    return 'OK'


#
# Endpoints for StanzaSyntaxEnsembleTaggerWorker
#

@app.post('/estnltk/tagger/stanza_syntax_ensemble')
def tagger_stanza_syntax_ensemble():
    if request.content_length > settings.MAX_CONTENT_LENGTH:
        abort(413)
    response = stanza_ensemble.process_request(content=request.json)
    return response


@app.get('/estnltk/tagger/stanza_syntax_ensemble/about')
def tagger_stanza_syntax_ensemble_about():
    return 'Tags dependency syntactic analysis using EstNLTK StanzaSyntaxEnsembleTagger\'s webservice.'


@app.get('/estnltk/tagger/stanza_syntax_ensemble/status')
def tagger_stanza_syntax_ensemble_status():
    return 'OK'


if __name__ == '__main__':
    app.run()
