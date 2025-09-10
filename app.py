import streamlit as st
import snowflake.connector

conn = snowflake.connector.connect(
    account=st.secrets["snowflake"]["account"],
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    role=st.secrets["snowflake"]["role"],
    warehouse=st.secrets["snowflake"]["warehouse"],
    database=st.secrets["snowflake"]["database"],
    schema=st.secrets["snowflake"]["schema"],
)

def get_factor(sides):
    """Get settlement factor based on number of settled sides."""
    if sides == 1:
        return 0.5
    elif sides == 2:
        return 0.75
    else:  # 3 or 4 sides: near-uniform
        return 1.0

# Set up the webpage title and description
st.title("🛠️ Concrete Lifting Polyfoam Cost Estimator")
st.write("Enter the slab details below to get an estimate. All calculations are based on standard industry formulas.")

# Create input fields (like a form)
st.sidebar.header("Inputs")  # Puts inputs on the side for a clean look
width = st.sidebar.number_input("Width of slab (feet)", min_value=0.1, value=10.0, step=0.1)
length = st.sidebar.number_input("Length of slab (feet)", min_value=0.1, value=10.0, step=0.1)
sides = st.sidebar.selectbox("How many sides of the slab have settled", options=[1, 2, 3, 4], index=1)
settlement_inches = st.sidebar.number_input("Settlement at lowest point (inches)", min_value=0.1, value=1.0, step=0.1)
price_per_lb = st.sidebar.number_input("Price per pound of polyfoam ($)", min_value=0.01, value=2.0, step=0.01)

# Add a "Calculate" button
if st.sidebar.button("Calculate Estimate"):
    # Calculations (same as before)
    area_sqft = width * length
    factor = get_factor(sides)
    avg_settlement_inches = settlement_inches * factor
    avg_settlement_ft = avg_settlement_inches / 12
    
    # Cubic yards of polyfoam (expanded volume to fill void)
    volume_cuft = area_sqft * avg_settlement_ft
    volume_cuyards = volume_cuft / 27
    
    # Pounds of polyfoam (material used, per rule of thumb)
    pounds = area_sqft * avg_settlement_inches  # 1 lb per sqft per inch average lift
    
    # Total cost
    total_cost = pounds * price_per_lb
    
    # Display results on the main page
    st.header("Estimation Results")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Slab Area", f"{area_sqft:.2f} sq ft")
        st.metric("Average Settlement Depth", f"{avg_settlement_inches:.2f} inches (factor: {factor})")
    with col2:
        st.metric("Cubic Yards of Polyfoam Required", f"{volume_cuyards:.2f}")
        st.metric("Pounds of Polyfoam Used", f"{pounds:.2f}")
    
    st.metric("Estimated Material Cost", f"${total_cost:.2f}")
    st.write("*Note: This is an estimate. Consult a professional for accurate assessments.*")
else:
    st.info("👈 Enter values in the sidebar and click 'Calculate Estimate' to see results.")

# Add a sample example
with st.expander("Try This Sample (10x10 ft slab, 2 sides, 1 inch settlement, $2/lb)"):
    st.write("Expected: 0.23 cubic yards, 75 lbs, $150 cost.")

