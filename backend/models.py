import datetime # for the created at time stamp
from sqlalchemy import String, Float, Boolean, DateTime, JSON # col types
from sqlalchemy.orm import mapped_column, Mapped # for type of col
from database import Base # inherit base class created in database.py

class AnalysisLog(Base): # inherits from Base, one class = one table
    __tablename__ = "analysis_logs" # name of table in postgres
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True) # ID col that uniquely identifies each row, no two rows can have same ID, rows assigned in increasing order 1,2,3..
    image_hash: Mapped[str] = mapped_column(String, nullable=False) # store unique image hash, every row MUST have an image hash
    huggingface_output: Mapped[dict] = mapped_column(JSON, nullable=True) # stores vision response from HuggingFace, optional so if API fails can still save log col empty for notes
    gemini_output: Mapped[dict] = mapped_column(JSON, nullable=True) # stores gemini API response, optional so if API fails can still save log col empty
    final_output: Mapped[dict] = mapped_column(JSON, nullable=True) # stores what safety layer produces after validated response, optional so if API fails can still save log col empty
    requires_special_handling: Mapped[bool] = mapped_column(Boolean, default=False) # true if safety layer flagged the item as hazardous, default false so assume safe
    clarification_needed: Mapped[bool] = mapped_column(Boolean, default=False) # true if the HuggingFace confidence was too low and the system needs more user info
    confidence: Mapped[float] = mapped_column(Float, nullable=True) # stores confidence score from HuggingFace, if fails entirely theres no score to save
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow) # time stamp for when the row was created