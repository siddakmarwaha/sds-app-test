from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jyotishyamitra as jsm
import json
import os
import tempfile
from datetime import datetime

app = FastAPI(title="SoulDoctor Astrology API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class BirthData(BaseModel):
    name: str
    gender: str
    dob: str       # "YYYY-MM-DD"
    tob: str       # "HH:MM"
    latitude: float
    longitude: float
    timezone: float


# Map numeric month → library constant
MONTH_MAP = {
    1: jsm.January,
    2: jsm.February,
    3: jsm.March,
    4: jsm.April,
    5: jsm.May,
    6: jsm.June,
    7: jsm.July,
    8: jsm.August,
    9: jsm.September,
    10: jsm.October,
    11: jsm.November,
    12: jsm.December,
}


@app.post("/chart")
def generate_chart(data: BirthData):
    try:
        jsm.clear_birthdata()

        # Parse datetime safely
        try:
            dt = datetime.strptime(f"{data.dob} {data.tob}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date/time format")

        month_constant = MONTH_MAP.get(dt.month)
        if not month_constant:
            raise HTTPException(status_code=400, detail="Invalid month")

        # Input birth data with correct types
        jsm.input_birthdata(
            name=data.name,
            gender=data.gender.lower(),
            year=dt.year,
            month=month_constant,
            day=dt.day,
            hour=dt.hour,
            min=dt.minute,
            sec=0,
            place="CustomLocation",
            longitude=data.longitude,
            lattitude=data.latitude,   # library typo
            timezone=data.timezone,
        )

        # VALIDATE (you skipped this earlier)
        jsm.validate_birthdata()

        if not jsm.IsBirthdataValid():
            raise HTTPException(status_code=400, detail="Birth data validation failed")

        birthdata = jsm.get_birthdata()
        if birthdata is None:
            raise HTTPException(status_code=400, detail="Birth data not generated")

        # Generate to temp file (most reliable method)
        with tempfile.TemporaryDirectory() as tmpdir:

            status = jsm.set_output(path=tmpdir, filename="chart")
            if status != "SUCCESS":
                raise HTTPException(status_code=500, detail="Output path setup failed")

            result = jsm.generate_astrologicalData(birthdata)

            # Case 1: library returned dict
            if isinstance(result, dict):
                return {"success": True, "data": result}

            # Case 2: file mode
            output_file = jsm.get_output()

            if not output_file or not os.path.exists(output_file):
                raise HTTPException(status_code=500, detail="Chart file not created")

            with open(output_file, "r") as f:
                astro_data = json.load(f)

            return {"success": True, "data": astro_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
