import logging
from typing import Dict

from nauron import Response, Worker
from marshmallow import Schema, fields, ValidationError

from estnltk import Text
from estnltk.converters import layer_to_dict
from estnltk.converters import json_to_layers

from ensemble_tagger import StanzaSyntaxEnsembleTagger

import settings

logger = logging.getLogger(settings.SERVICE_NAME)


class StanzaSyntaxEnsembleTaggerRequestSchema(Schema):
    text = fields.Str(required=True)
    meta = fields.Raw(required=True)
    layers = fields.Str(required=True)
    output_layer = fields.Str(required=False)
    parameters = fields.Raw(required=False, allow_none=True)


class StanzaSyntaxEnsembleTaggerWorker(Worker):
    def __init__(self, resources_dir: str = "stanza_resources/"):
        self.schema = StanzaSyntaxEnsembleTaggerRequestSchema
        self.tagger = StanzaSyntaxEnsembleTagger(dir=resources_dir)

    def process_request(self, content: Dict, _: str) -> Response:
        try:
            logger.debug(content)
            content = self.schema().load(content)
            text = Text(content["text"])
            text.meta = content["meta"]
            layers = json_to_layers(text, json_str=content['layers'])
            for layer in Text.topological_sort(layers):
                text.add_layer(layer)
            layer = self.tagger.make_layer(text, layers)
            if 'output_layer' in content.keys():
                layer.name = content['output_layer']
            # No need to do layer_to_json: Response obj will handle the conversion
            return Response(layer_to_dict(layer), mimetype="application/json")
        except ValidationError as error:
            return Response(content=error.messages, http_status_code=400)
        except ValueError as err:
            # If tagger.make_layer throws a ValueError, report about a missing layer
            return Response(content='Error at input processing: {}'.format(str(err)), http_status_code=400)
        except Exception as error:
            return Response(content='Internal error at input processing', http_status_code=400)


if __name__ == "__main__":
    worker = StanzaSyntaxEnsembleTaggerWorker(resources_dir=settings.MODEL_PATH)
    worker.start(connection_parameters=settings.MQ_PARAMS,
                 service_name="ensemble"+settings.SERVICE_NAME,
                 routing_key=settings.ROUTING_KEY)
