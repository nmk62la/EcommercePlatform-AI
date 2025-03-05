from flask import Blueprint, jsonify, request
from app.services.product_service import recommend_collaborative, recommend_contentbased
from app.models.product import DatabaseConnection

product_controller = Blueprint('product_controller', __name__)

@product_controller.route('/api/v1/ai/recommend/list_product', methods=['GET'])
def api_recommend_collaborative():
    limit_all = 24
    limit_one = 6
    limit_user = 4
    current_user_id = request.args.get("user_id")
    print(f"current_user_id: ", current_user_id)

    if not current_user_id:
        return jsonify({"code": 1001, "message": "User not found"}), 400
    
    dbConnection = DatabaseConnection()

    df_user_item = dbConnection.get_df_user_item()
    print(f"df_user_item:\n {df_user_item}")
    
    suggested_ids = recommend_collaborative(df_user_item, current_user_id, limit_all, limit_one, limit_user)
    print(f"suggested_ids: {suggested_ids}")

    listProduct = dbConnection.get_response_list_product(suggested_ids)

    return jsonify({"code": 1000, "result": listProduct})

@product_controller.route('/api/v1/ai/recommend/product', methods=['GET'])
def api_recommend_contentbased():
    limit_all = 24
    current_product_id = request.args.get("product_id")
    print(f"current_product_id: ", current_product_id)

    if not current_product_id:
        return jsonify({"code": 1001,"message": "Product not found"}), 400

    dbConnection = DatabaseConnection()

    df_item = dbConnection.get_df_item()
    print(f"df_item:\n {df_item}")
    
    suggested_ids = recommend_contentbased(df_item, current_product_id, limit_all)
    print(f"suggested_ids: ", suggested_ids)

    listProduct = dbConnection.get_response_list_product(suggested_ids)

    return jsonify({
        "code": 1000,
        "interacted": current_product_id,
        "result": listProduct
        })