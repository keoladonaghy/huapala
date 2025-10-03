#!/usr/bin/env python3
"""Clear partial migration data"""

import os
from sqlalchemy import create_engine
from database import get_database_url, Verses, VerseLines, VerseProcessingMetadata
from sqlalchemy.orm import sessionmaker

engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Clear any partial data
session.query(VerseLines).delete()
session.query(Verses).delete() 
session.query(VerseProcessingMetadata).delete()
session.commit()
session.close()
print('Cleared partial migration data')