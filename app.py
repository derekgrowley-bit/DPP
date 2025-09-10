import streamlit as st
import snowflake.connector

st.set_page_config(page_title="Polyfoam Estimator + Snowflake Test", page_icon="🛠️", layout="centered")

# -----------------------------
# 1) Snowflake connection (safe & debuggable)
# -----------------------------
st.header("🔎 Snowflake Cloud Connect Test")

@st.cache_resource(show_spinner=False)
def get_conn():
    """Create and cache a Snowflake connection using Streamlit secrets."""
    sf = st.secrets["snowflake"]  # read inside so the cache key is stable
    return snowflake.connector.connect(
        account=sf["account"],
        user=sf["user"],
        password=sf["password"],
        role=sf["role"],
        warehouse=sf["warehouse"],
        database=sf["database"],
        schema=sf["schema"],
    )

if st.button("Connect to Snowflake"):
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Authentication / context smoke test
        cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
        st.success(("Connected:",) + cur.fetchone())

        # Optional demo read to prove data access
        try:
            cur.execute("SELECT * FROM STREAMLIT_DB.APPDATA.HELLO_DEMO")
            st.dataframe(cur.fetchall(), use_container_width=True)
        except Exception as e:
            st.warning("Connected, but could not read STREAMLIT_DB.APPDATA.HELLO_DEMO.")
            st.code(repr(e))

    except Exception as e:
        st.error("❌ Connect failed. Check Cloud Secrets, user password/lock, or network policy.")
        st.code(repr(e))

st.divider()

# -----------------------------
# 2) Your estimator UI (works even if Snowflake is down)
# -----------------------------
def get_factor(sides: int) -> float:
    """
    Simple rule of thumb for average lift vs. max settlement depth.
    Adjust if you prefer 3-sides ≈ 0.90 instead of 1.00.
    """
    return {1: 0.50, 2: 0.75, 3: 1.00, 4: 1.00}.get(int(sides), 0.75)

st.title("🛠️ Concrete Lifting Polyfoam Cost Estimator")
st.write("Enter the slab details below to get an estimate. These are rule-of-thumb calculations.")

# Sidebar inputs
st.sidebar.header("Inputs")
width = st.sidebar.number_input("Width of slab (feet)", min_value=0.1, value=10.0, step=0.1)
length = st.sidebar.number_input("Length of slab (feet)", min_value=0.1, value=10.0, step=0.1)
sides = st.sidebar.selectbox("How many sides of the slab have settled", options=[1, 2, 3, 4], index=1)
settlement_inches = st.sidebar.number_input("Settlement at lowest point (inches)", min_value=0.1, value=1.0, step=0.1)
price_per_lb = st.sidebar.number_input("Price per pound of polyfoam ($)", min_value=0.01, value=2.0, step=0.01)

if st.sidebar.button("Calculate Estimate"):
    # Core math
    area_sqft = width * length
    factor = get_factor(sides)
    avg_settlement_inches = settlement_inches * factor
    avg_settlement_ft = avg_settlement_inches / 12.0

    # Volumes
    volume_cuft = area_sqft * avg_settlement_ft
    volume_cuyards = volume_cuft / 27.0

    # Material & cost
    pounds = area_sqft * avg_settlement_inches   # ≈ 1 lb/sqft per inch avg lift
    total_cost = pounds * price_per_lb

    # Results
    st.header("Estimation Results")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Slab Area", f"{area_sqft:.2f} sq ft")
        st.metric("Average Settlement Depth", f"{avg_settlement_inches:.2f} in (factor: {factor:.2f})")
    with col2:
        st.metric("Cubic Yards Required", f"{volume_cuyards:.2f}")
        st.metric("Pounds of Polyfoam", f"{pounds:.2f}")

    st.metric("Estimated Material Cost", f"${total_cost:.2f}")
    st.caption("Note: Rule-of-thumb estimate. Site conditions may vary.")
else:
    st.info("👈 Enter values in the sidebar and click **Calculate Estimate** to see results.")

with st.expander("Try This Sample (10×10 ft slab, 2 sides, 1 inch, $2/lb)"):
    st.write("Expected ≈ 0.23 cubic yards, 75 lbs, $150 cost.")
