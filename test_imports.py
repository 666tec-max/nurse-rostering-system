import sys
import os

print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

try:
    import streamlit as st
    print("Streamlit imported")
except ImportError as e:
    print(f"Failed to import streamlit: {e}")

try:
    import pandas as pd
    print("Pandas imported")
except ImportError as e:
    print(f"Failed to import pandas: {e}")

try:
    import ortools
    print("OR-Tools imported")
except ImportError as e:
    print(f"Failed to import ortools: {e}")

try:
    from supabase import create_client, Client
    print("Supabase imported")
except ImportError as e:
    print(f"Failed to import supabase: {e}")

try:
    import staff_db
    print("staff_db imported")
except ImportError as e:
    print(f"Failed to import staff_db: {e}")
    import traceback
    traceback.print_exc()

try:
    import auth_utils
    print("auth_utils imported")
except ImportError as e:
    print(f"Failed to import auth_utils: {e}")
    import traceback
    traceback.print_exc()

try:
    import leave_db
    print("leave_db imported")
except ImportError as e:
    print(f"Failed to import leave_db: {e}")
    import traceback
    traceback.print_exc()
