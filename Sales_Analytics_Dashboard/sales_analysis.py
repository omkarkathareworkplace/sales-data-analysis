import os
import sys
from urllib.parse import quote_plus
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# ==========================================
# CONFIGURATION
# ==========================================
DB_USER = "root"
DB_PASS = "admin@123"
DB_HOST = "localhost"
DB_NAME = "sales_analytics"
OUTPUT_DIR = "dashboard"


def get_db_engine():
    """Creates and returns a SQLAlchemy database engine safely handling special characters."""
    # Escapes special characters like '@' in passwords
    encoded_pass = quote_plus(DB_PASS)
    connection_uri = f"mysql+pymysql://{DB_USER}:{encoded_pass}@{DB_HOST}/{DB_NAME}"
    return create_engine(connection_uri)


def generate_top_products_chart(engine):
    """Generates a horizontal bar chart of the top 10 selling products."""
    query = """
        SELECT
            p.product_name,
            SUM(od.quantity) AS total_sold
        FROM products p
        JOIN order_details od ON p.product_id = od.product_id
        GROUP BY p.product_id, p.product_name
        ORDER BY total_sold ASC
        LIMIT 10;
    """
    df = pd.read_sql(query, engine)
    
    fig = px.bar(
        df,
        x="total_sold",
        y="product_name",
        orientation="h",
        title="Top 10 Selling Products",
        text="total_sold",
        labels={"total_sold": "Units Sold", "product_name": "Product"}
    )
    fig.update_layout(template="plotly_dark", height=600)
    fig.write_html(os.path.join(OUTPUT_DIR, "top_products.html"))


def generate_monthly_revenue_chart(engine):
    """Generates a line chart showing monthly revenue trends."""
    query = """
        SELECT
            MONTH(o.order_date) AS month_number,
            MONTHNAME(o.order_date) AS month_name,
            SUM(od.quantity * od.sale_price) AS monthly_revenue
        FROM orders o
        JOIN order_details od ON o.order_id = od.order_id
        GROUP BY MONTH(o.order_date), MONTHNAME(o.order_date)
        ORDER BY month_number;
    """
    df = pd.read_sql(query, engine)
    
    fig = px.line(
        df,
        x="month_name",
        y="monthly_revenue",
        markers=True,
        title="Monthly Revenue Trend",
        labels={"month_name": "Month", "monthly_revenue": "Revenue ($)"}
    )
    fig.update_layout(template="plotly_dark", height=600)
    fig.update_yaxes(tickprefix="$", tickformat=",.")
    fig.write_html(os.path.join(OUTPUT_DIR, "monthly_revenue.html"))


def generate_top_customers_chart(engine):
    """Generates a bar chart of the top 10 customers by spend."""
    query = """
        SELECT
            c.customer_name,
            SUM(od.quantity * od.sale_price) AS total_spent
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_details od ON o.order_id = od.order_id
        GROUP BY c.customer_id, c.customer_name
        ORDER BY total_spent DESC
        LIMIT 10;
    """
    df = pd.read_sql(query, engine)
    
    fig = px.bar(
        df,
        x="customer_name",
        y="total_spent",
        title="Top 10 Customers by Revenue",
        labels={"customer_name": "Customer", "total_spent": "Total Spent ($)"},
        text_auto="$,.2f"
    )
    fig.update_layout(template="plotly_dark", height=600)
    fig.write_html(os.path.join(OUTPUT_DIR, "top_customers.html"))


def generate_city_revenue_chart(engine):
    """Generates a pie chart of revenue distribution across cities."""
    query = """
        SELECT
            c.city,
            SUM(od.quantity * od.sale_price) AS city_revenue
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_details od ON o.order_id = od.order_id
        GROUP BY c.city
        ORDER BY city_revenue DESC;
    """
    df = pd.read_sql(query, engine)
    
    fig = px.pie(
        df,
        names="city",
        values="city_revenue",
        title="Revenue Distribution by City",
        hole=0.3
    )
    fig.update_layout(template="plotly_dark", height=600)
    fig.update_traces(textinfo="percent+label", hovertemplate="%{label}: $%{value:,.2f}")
    fig.write_html(os.path.join(OUTPUT_DIR, "city_revenue.html"))


def main():
    """Main execution pipeline."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        print("Connecting to database...")
        engine = get_db_engine()
        
        print("Generating charts...")
        generate_top_products_chart(engine)
        generate_monthly_revenue_chart(engine)
        generate_top_customers_chart(engine)
        generate_city_revenue_chart(engine)
        
        print("✅ Professional charts created successfully!")
        print(f"📂 Output saved in the '{OUTPUT_DIR}' directory.")
        
    except SQLAlchemyError as e:
        print(f"❌ Database error encountered: {e}", file=sys.stderr)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        if 'engine' in locals():
            engine.dispose()


if __name__ == "__main__":
    main()