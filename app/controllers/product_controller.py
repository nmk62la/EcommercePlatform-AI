from flask import Blueprint, request
from app.services.product_service import recommend_collaborative, recommend_contentbased
from app.models.product import DatabaseConnection

product_controller = Blueprint('product_controller', __name__)

@product_controller.route('/api/v1/ai/recommend/list_product', methods=['GET'])
def api_recommend_collaborative():
    limit_all = max(24, int(request.args.get("limit_all")))
    limit_user = max(24, int(request.args.get("limit_user")))
    limit_one = max(24, int(request.args.get("limit_one")))
    current_user_id = request.args.get("user_id")
    page = request.args.get("page")
    size = request.args.get("size")

    dbConnection = DatabaseConnection()

    df_user_item = dbConnection.get_df_user_item()
    # print(f"df_user_item:\n {df_user_item}")

    suggested_ids = recommend_collaborative(df_user_item, current_user_id, page, size, limit_all, limit_one, limit_user)
    # print(f"suggested_ids: {suggested_ids}")

    return dbConnection.get_response_list_product(suggested_ids, page, size)

@product_controller.route('/api/v1/ai/recommend/product', methods=['GET'])
def api_recommend_contentbased():
    limit_all = max(24, int(request.args.get("limit_all")))
    page = request.args.get("page")
    size = request.args.get("size")
    current_product_id = request.args.get("product_id")

    if not current_product_id:
        return {
            "data": [],
            "totalPages": 0,
            "pageSize": size,
            "totalElements": 0,
            "currentPage": page,
            "hasNext": False,
            "hasPrevious": False,
            "nextPage": False,
            "previousPage": False
        }

    dbConnection = DatabaseConnection()

    df_item = dbConnection.get_df_item()
    # print(f"df_item:\n {df_item}")

    suggested_ids = recommend_contentbased(df_item, current_product_id, page, size, limit_all)
    # print(f"suggested_ids: ", suggested_ids)

    return dbConnection.get_response_list_product(suggested_ids, page, size)