from fastapi import FastAPI
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

app = FastAPI()

class GameState(BaseModel):
    tahta: List[List[int]]
    oyun_sirasi: str
    son_hamle: Optional[List[Any]] # [sr, sc, br, bc, stas] formatında
    rok_durumu: Dict[str, Dict[str, bool]]

# Başlangıç durumu
initial_state = {
    "tahta": [
        [-2,-3,-4,-5,-6,-4,-3,-2],
        [-1,-1,-1,-1,-1,-1,-1,-1],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [1,1,1,1,1,1,1,1],
        [2,3,4,5,6,4,3,2]
    ],
    "oyun_sirasi": "white",
    "son_hamle": None,
    "rok_durumu": {
        "white": {"K": False, "R1": False, "R2": False},
        "black": {"K": False, "R1": False, "R2": False}
    }
}

current_state = initial_state.copy()

@app.post("/state")
def update_state(payload: GameState):
    global current_state
    current_state = payload.model_dump()
    return {"message": "State updated", "current_state": current_state}

@app.get("/state")
def get_state():
    return current_state

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)

