import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from underthesea import word_tokenize
from flask import jsonify, request
import json

def recommend_collaborative(df_user_item, current_user_id, limit_all, limit_one, limit_user):
    if df_user_item is None:
        return []

    df_user_item = df_user_item.infer_objects()

    user_item_matrix = df_user_item.pivot_table(index='user_id', columns='product_id', values='score', fill_value=0)
    print(f"user_item_matrix:\n {user_item_matrix}")

    if user_item_matrix.empty:
        return []

    user_similarity = cosine_similarity(user_item_matrix)
    print(f"user_similarity:\n {user_similarity}")

    user_ids = user_item_matrix.index
    print(f"user_ids:\n {user_ids}")

    df_similarity = pd.DataFrame(user_similarity, index=user_ids, columns=user_ids)
    print(f"df_similarity:\n {df_similarity}")

    if current_user_id not in df_similarity.index:
        return []

    # Lấy danh sách similar_users tương tự current_user
    similar_users = df_similarity.loc[current_user_id].nlargest(limit_user + 1).index[1:]
    print(f"similar_users:\n {similar_users}")

    # Lấy danh sách products mà similar_users đã tương tác
    similar_users_products = df_user_item[df_user_item['user_id'].isin(similar_users)].copy()
    print(f"similar_users_products:\n {similar_users_products}")

    # Gán thứ tự xuất hiện của từng user dựa vào danh sách similar_users
    similar_users_products["user_order"] = similar_users_products["user_id"].astype("category")
    similar_users_products["user_order"] = similar_users_products["user_order"].cat.set_categories(similar_users, ordered=True)
    similar_users_products["user_order"] = similar_users_products["user_order"].cat.codes

    # Sắp xếp theo thứ tự của similar_users và score
    similar_users_products = similar_users_products.sort_values(by=["user_order", "score"], ascending=[True, False])
    print(f"similar_users_products (sx theo similar_users và score):\n {similar_users_products}")

    # Loại bỏ sản phẩm trùng lặp
    similar_users_products = similar_users_products.drop_duplicates(subset=['product_id'], keep='first')

    # Giữ tối đa limit_one sản phẩm cho mỗi similar_users
    similar_users_products = similar_users_products.groupby("user_id").head(limit_one)
    print(f"similar_users_products (đã lọc & giới hạn sản phẩm/user):\n {similar_users_products}")

    # Giới hạn tổng số sản phẩm gợi ý không quá limit_all
    limit_products = similar_users_products.head(limit_all)
    print(f"limit_products:\n {limit_products}")

    # Trả về danh sách product_id của các sản phẩm gợi ý
    suggested_product_ids = limit_products['product_id'].tolist()

    return suggested_product_ids

# Hàm tokenizer tùy chỉnh sử dụng underthesea
def vietnamese_tokenizer(text):
    return word_tokenize(text)

# Danh sách từ dừng
with open('vietnamese-stopwords.txt', 'r', encoding='utf-8') as file:
    vietnamese_stop_words = [line.strip() for line in file]

# Khởi tạo TfidfVectorizer với tokenizer tùy chỉnh và từ dừng
tfidf = TfidfVectorizer(
    tokenizer=vietnamese_tokenizer,
    stop_words=vietnamese_stop_words,
    lowercase=True
)
tfidf_matrix = None
cosine_sim = None

def recommend_contentbased(df_item, product_id, limit_all):
    if product_id not in df_item["product_id"].values:
        return []

    global tfidf_matrix, cosine_sim

    if tfidf_matrix is None or cosine_sim is None:
        tfidf_matrix = tfidf.fit_transform(df_item["content"])
        print(f"tfidf_matrix: {tfidf_matrix}")

        cosine_sim = cosine_similarity(tfidf_matrix)
        print(f"cosine_sim: {cosine_sim}")

    suggested_product_ids = []

    similar_products = get_products_similar(df_item, product_id, cosine_sim, limit_all)
    print(f"similar_products: ", similar_products)

    for pid in similar_products['product_id'].tolist():
        if pid not in suggested_product_ids:
            suggested_product_ids.append(pid)

    return suggested_product_ids

def get_products_similar(df_item, product_id, cosine_sim, limit_all):
    idx = df_item[df_item['product_id'] == product_id].index[0]
    print(f"idx: {idx}")

    sim_scores = list(enumerate(cosine_sim[idx]))
    print(f"sim_scores: {sim_scores}")

    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    print(f"sim_scores đã sort: {sim_scores}")

    sim_scores = sim_scores[1:limit_all+1]
    print(f"sim_scores đã bỏ nó: {sim_scores}")

    product_indices = [i[0] for i in sim_scores]
    print(f"product_indices: {product_indices}")

    return df_item.iloc[product_indices]

def chatbot(file_path):
    config = load_chatbot_config(file_path)
    if not config:
        return jsonify({"error": "Không thể tải cấu hình chatbot"}), 500

    data = request.get_json()
    selected_id = data.get('selected_id') if data else None

    if not selected_id:
        # Trả về danh sách tùy chọn ban đầu
        return jsonify({
            "message": config['name_title'],
            "has_next": config.get('has_next', False),
            "is_ai": True,
            "options": [
                {"id": opt['id'], "title": opt['title'], "has_next": opt.get('has_next', False)}
                for opt in config.get('options', [])
            ]
        })

    # Tìm tùy chọn được chọn theo ID
    selected_option = find_option_by_id(config.get('options', []), selected_id)
    if not selected_option:
        return jsonify({"error": f"ID '{selected_id}' không hợp lệ"}), 400

    # Trả về phản hồi
    response = {
        "message": selected_option['name_title'],
        "has_next": selected_option.get('has_next', False),
        "is_ai": True,
    }
    if selected_option.get('has_next', False):
        response["options"] = [
            {"id": opt['id'], "title": opt['title'], "has_next": opt.get('has_next', False)}
            for opt in selected_option.get('options', [])
        ]
    else:
        response["answer"] = selected_option.get('answer', '')
        response["has_chat_with_shop"] = selected_option.get('has_chat_with_shop', False)

    return jsonify(response)

def load_chatbot_config(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data['chatbot_config']
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

def find_option_by_id(options, target_id):
    # Tìm tùy chọn theo ID trong cây cấu trúc lồng nhau
    for option in options:
        if option['id'] == target_id:
            return option
        if 'options' in option:
            result = find_option_by_id(option['options'], target_id)
            if result:
                return result
    return None