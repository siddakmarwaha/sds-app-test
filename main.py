from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jyotishyamitra
import json
import os
import tempfile

app = FastAPI(title="SoulDoctor Astrology API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class BirthData(BaseModel):
    name: str
    gender: str  # "male" or "female"
    dob: str     # "YYYY-MM-DD"
    tob: str     # "HH:MM" (24hr format)
    latitude: float
    longitude: float
    timezone: float  # e.g. 5.5 for IST


@app.post("/chart")
def generate_chart(data: BirthData):
    try:
        # Step 1: Clear previous data
        jyotishyamitra.clear_birthdata()

        # Step 2: Parse date and time
        year, month, day = data.dob.split("-")
        hour, minute = data.tob.split(":")
        sec = "0"

        # Step 3: Input birth data
        jyotishyamitra.input_birthdata(
            name=data.name,
            gender=data.gender,
            year=year,
            month=str(int(month)),
            day=str(int(day)),
            hour=str(int(hour)),
            min=str(int(minute)),
            sec=sec,
            place="CustomLocation",
            longitude=str(data.longitude),
            lattitude=str(data.latitude),  # note: library uses 'lattitude' (typo in lib)
            timezone=f"+{data.timezone}" if data.timezone >= 0 else str(data.timezone),
        )
        tz_str = f"+{data.timezone}" if data.timezone >= 0 else str(data.timezone)
        inputdata = jyotishyamitra.input_birthdata(name="Shyam Bhat", gender="male", year="1991", month=jyotishyamitra.October, day="8", hour="14", min="47", sec="9", place="Honavar", longitude="+74.4439", lattitude="+14.2798", timezone="+5.5")
        print(inputdata)
        print(jyotishyamitra.validate_birthdata())
        print(f"input_birthdata called with: name={data.name}, gender={data.gender}, "f"year={year}, month={str(int(month))}, day={str(int(day))}, hour={str(int(hour))}, min={str(int(minute))}, "f"lon={str(data.longitude)}, lat={str(data.latitude)}, tz={tz_str}")
          
        try:
            birthdata = jyotishyamitra.get_birthdata()
            print(f"birthdata result: {birthdata}")
        except Exception as e:
            print(e)

        # Step 4: Validate birth data
        birthdata = jyotishyamitra.get_birthdata()
        if birthdata is None:
            raise HTTPException(status_code=400, detail="Invalid birth data")

        # Step 5: Generate chart — try dictionary output first
        try:
            astro_data = jyotishyamitra.generate_astrologicalData(birthdata)
            if astro_data and isinstance(astro_data, dict):
                return {"success": True, "data": astro_data}
        except Exception:
            pass

        # Fallback: generate to temp JSON file and read it
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "chart.json")
            jyotishyamitra.set_output(path=tmpdir, filename="chart")
            jyotishyamitra.generate_astrologicalData(birthdata)

            if os.path.exists(output_path):
                with open(output_path, "r") as f:
                    astro_data = json.load(f)
                return {"success": True, "data": astro_data}

        raise HTTPException(status_code=500, detail="Failed to generate chart")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
