#!/usr/bin/env python3
"""Debug why the migration is failing"""

import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import get_database_url, MeleSources

# Database setup
DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Get the first song that's failing
source = session.query(MeleSources).filter(MeleSources.id == 'adios_ke_aloha_canonical_source').first()

if source:
    print(f"Analyzing: {source.id}")
    
    verses_data = source.verses_json
    if isinstance(verses_data, str):
        verses_data = json.loads(verses_data)
    
    verses = verses_data.get('verses', [])
    print(f"Found {len(verses)} verses:")
    
    order_counts = {}
    for verse in verses:
        verse_order = verse.get('order', 1)
        if verse_order in order_counts:
            order_counts[verse_order] += 1
        else:
            order_counts[verse_order] = 1
        
        print(f"  ID: {verse.get('id')}, Type: {verse.get('type')}, Number: {verse.get('number')}, Order: {verse_order}")
    
    print(f"\nOrder frequency:")
    for order, count in sorted(order_counts.items()):
        if count > 1:
            print(f"  ⚠️  Order {order}: {count} verses (CONFLICT!)")
        else:
            print(f"  ✅ Order {order}: {count} verse")
            
else:
    print("Song not found")

session.close()