"""Final FastAPI JSON boundary, shared by every registered HTTP API route."""
import json
import logging
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from game.player_http_projection import GENERIC_ERROR, project_player_response

log = logging.getLogger(__name__)


class PlayerHTTPRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handle(request):
            if not request.url.path.startswith('/api/'):
                return await original(request)
            try:
                response = await original(request)
                # No streaming or non-JSON internal API responses are authorized.
                payload = json.loads(response.body)
                content = project_player_response(payload)
                headers = {k:v for k,v in response.headers.items()
                           if k.lower() not in ('content-length','content-type')}
                final = JSONResponse(content=content,status_code=response.status_code,
                                    headers=headers,background=response.background)
            except RequestValidationError:
                final = JSONResponse(status_code=422,content={'ok':False,'error':'Check the request fields and try again.'})
            except HTTPException as error:
                final = JSONResponse(status_code=error.status_code,content={'ok':False,'error':GENERIC_ERROR})
            except Exception:
                # Detailed exceptions stay in server logs. Never serialize input,
                # exception text, stack frames, prompts or partial internal state.
                log.exception('Player HTTP request failed: %s', request.url.path)
                final = JSONResponse(status_code=500,content={'ok':False,'error':GENERIC_ERROR})
            if (request.url.path in {'/api/chat','/api/action','/api/start_campaign'}
                    and not getattr(request.state, 'skip_publication_trace', False)):
                from game.publication_contract import record_completed_publication
                provenance = getattr(request.state, 'publication_provenance', None) or {
                    'source_handler': request.url.path}
                try:
                    record_completed_publication(final, **provenance)
                except OSError:
                    # Observability failure cannot undo an already committed turn
                    # or turn success into a retry that would repeat gameplay.
                    log.exception('Completed publication trace write failed')
            return final

        return handle
