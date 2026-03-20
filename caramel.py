from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home(i: int):
	a = 10
	b = "silli Billi"
	c = {'a':'bili ka nakh', 'b':'sili ka daat', 'c': 'haat maar bas'}
	return a if (i ==1) else c,b	
