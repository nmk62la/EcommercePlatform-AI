import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

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
    
    # Lấy danh sách products mà current_user đã tương tác
    current_user_products = df_user_item[df_user_item['user_id'] == current_user_id]["product_id"].tolist()
    print(f"current_user_products:\n {current_user_products}")

    # Loại bỏ products mà current_user đã tương tác ra khỏi similar_users_products
    similar_users_products = similar_users_products.set_index("product_id").drop(current_user_products, errors="ignore").reset_index()
    print(f"similar_users_products (đã loại bỏ products của current_user):\n {similar_users_products}")

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

tfidf = TfidfVectorizer()
tfidf_matrix = None
cosine_sim = None

def recommend_contentbased(df_item, product_id, limit_all):
    if product_id not in df_item["product_id"].values:
        return []

    global tfidf_matrix, cosine_sim

    if tfidf_matrix is None or cosine_sim is None:
        tfidf_matrix = tfidf.fit_transform(df_item["item"])
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