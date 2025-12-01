using System;
using System.Web;

namespace DrinkShopWeb
{
    public partial class SaveCustomer : System.Web.UI.Page
    {
        protected void Page_Load(object sender, EventArgs e)
        {
            // 只處理第一次進來
            if (IsPostBack) return;

            // 1) 讀取表單資料：name="phone"
            string phone = Request.Form["phone"];

            // 2) 檢查是不是空的
            if (string.IsNullOrWhiteSpace(phone))
            {
                Response.Write("電話不得為空");
                return;   // 不再往下跑
            }

            // 3) 先不連資料庫，先確認流程
            //    直接導到點餐頁，順便把電話帶過去
            string url = "customer_order.html?phone=" + HttpUtility.UrlEncode(phone);
            Response.Redirect(url, true);
        }
    }
}
