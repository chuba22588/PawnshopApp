from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime


# --- DATABASE SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./amanet.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- THE TABLES ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nume = Column(String)
    rol = Column(String)

class AmanetItem(Base):
    __tablename__ = "obiecte_amanet"
    id = Column(Integer, primary_key=True, index=True)
    nume = Column(String)
    categorie = Column(String)
    pret = Column(Float)
    status = Column(String, default="disponibil")
    rezervat_de_id = Column(Integer, nullable=True)
    data_scadenta = Column(String, nullable=True)

class Tranzactie(Base):
    __tablename__ = "tranzactii"
    id = Column(Integer, primary_key=True, index=True)
    obiect_id = Column(Integer)
    user_id = Column(Integer)
    tip_tranzactie = Column(String)
    suma = Column(Float)
    data = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

Base.metadata.create_all(bind=engine)

# --- APP SETUP ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows Ngrok and your phone to connect!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_methods=["*"],
                   allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- ROUTES ---
@app.post("/adauga_user")
def create_user(nume: str, rol: str, db: Session = Depends(get_db)):
    nou_user = User(nume=nume, rol=rol)
    db.add(nou_user)
    db.commit()
    db.refresh(nou_user)
    return nou_user

@app.post("/adauga_obiect")
def create_item(nume: str, categorie: str, pret: float, data_scadenta: str = None, db: Session = Depends(get_db)):
    nou_obiect = AmanetItem(nume=nume,
                            categorie=categorie,
                            pret=pret,
                            data_scadenta=data_scadenta)
    db.add(nou_obiect)
    db.commit()
    db.refresh(nou_obiect)
    return nou_obiect

@app.get("/obiecte")
def get_items(db: Session = Depends(get_db)):
    return db.query(AmanetItem).all()

@app.get("/alerte")
def get_alerts(db: Session = Depends(get_db)):
    today = datetime.now().strftime("%Y-%m-%d")
    return db.query(AmanetItem).filter(AmanetItem.data_scadenta <= today, AmanetItem.status != "vandut").all()

@app.post("/adauga_tranzactie")
def creeaza_tranzactie(obiect_id: int, user_id: int, tip_tranzactie: str, suma: float, db: Session = Depends(get_db)):
    obiect = db.query(AmanetItem).filter(AmanetItem.id == obiect_id).first()
    if not obiect: return {"eroare": "Obiectul nu exista."}
    if tip_tranzactie.lower() == "vanzare": obiect.status = "vandut"
    elif tip_tranzactie.lower() == "amanet": obiect.status = "amanetat"
    noua_tranzactie = Tranzactie(obiect_id=obiect_id, user_id=user_id, tip_tranzactie=tip_tranzactie, suma=suma)
    db.add(noua_tranzactie)
    db.commit()
    return {"mesaj": f"Tranzactie de {tip_tranzactie} inregistrata!"}

@app.get("/schimb_valutar")
def calculeaza_schimb(suma: float, valuta: str):
    curs = {
        "EUR": 4.97, "USD": 4.65, "GBP": 5.80, "CHF": 5.10,
        "RSD": 0.042, "MDL": 0.26, "CAD": 3.45, "AUD": 3.05, "JPY": 0.031
    }
    v = valuta.upper()
    if v not in curs:
        return {"eroare": "Valuta nesuportata."}
    return {
        "suma_initiala": suma,
        "valuta": v,
        "total_ron": round(suma * curs[v], 2),
        "curs_folosit": curs[v]
    }