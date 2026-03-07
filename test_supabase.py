import sys
import os
import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

response = supabase.table("shifts").select("*").execute()
print("Shifts:", response.data)

response2 = supabase.table("staff").select("*").execute()
print("Staff len:", len(response2.data))

