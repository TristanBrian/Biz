from pydantic import BaseModel


class DashboardSummaryOut(BaseModel):
    today_sales: float
    sales_count: int
    low_stock_count: int
    upcoming_reminders: int
