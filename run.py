import uvicorn

from game.config import OPENAI_API_KEY  # loads .env if present

if __name__ == '__main__':
    # Print whether the API key is available at startup (do not print the key)
    print('OPENAI_API_KEY present:', bool(OPENAI_API_KEY))
    uvicorn.run('game.api:app', host='127.0.0.1', port=8000, reload=True)
