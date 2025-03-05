import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd

class DatabaseConnection:
    def __init__(self):
        load_dotenv()
        self.db_host = os.getenv("DB_HOST")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_port = int(os.getenv("DB_PORT"))

    def get_connection(self):
        try:
            connection = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port
            )
            return connection
        except Exception as e:
            print(f"Connect database fail: {str(e)}")
            return None
        
    def get_df_user_item(self):
        connection = self.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor()

            # Lấy dữ liệu từ bảng orders (trọng số = 4)
            order_query = """
                SELECT o.user_id, oi.product_id, COUNT(oi.id) AS order_count
                FROM orders o
                JOIN order_item oi ON o.id = oi.order_id
                JOIN product p ON oi.product_id = p.id
                WHERE o.is_deleted = FALSE
                AND oi.is_deleted = FALSE
                AND p.is_available = TRUE AND p.is_blocked = FALSE AND p.is_deleted = FALSE
                GROUP BY o.user_id, oi.product_id;
            """
            cursor.execute(order_query)
            order_data = cursor.fetchall()
            df_order = pd.DataFrame(order_data, columns=['user_id', 'product_id', 'order_count'])
            df_order['score'] = df_order['order_count'] * 4

            print(f"df_order:\n {df_order}")

            # Lấy dữ liệu từ bảng user_product_following (trọng số = 3)
            followings_query = """
                SELECT user_id, product_id, COUNT(upf.product_id) AS upf_count
                FROM user_product_following upf
                JOIN product p ON upf.product_id = p.id
                AND p.is_available = TRUE AND p.is_blocked = FALSE AND p.is_deleted = FALSE
                GROUP BY upf.user_id, upf.product_id;
            """
            cursor.execute(followings_query)
            followings_data = cursor.fetchall()
            df_followings = pd.DataFrame(followings_data, columns=['user_id', 'product_id', 'upf_count'])
            df_followings['score'] = df_followings['upf_count'] * 3

            print(f"df_followings:\n {df_followings}")

            # Lấy dữ liệu từ bảng cart (trọng số = 2)
            cart_query = """
                SELECT c.user_id, ci.product_id, COUNT(ci.id) AS cart_count
                FROM cart c
                JOIN cart_item ci ON c.id = ci.cart_id
                JOIN product p ON ci.product_id = p.id
                WHERE c.is_deleted = FALSE AND c.is_available = TRUE
                AND ci.is_deleted = FALSE AND ci.is_checkout = FALSE
                AND p.is_available = TRUE AND p.is_blocked = FALSE AND p.is_deleted = FALSE
                GROUP BY c.user_id, ci.product_id;
            """
            cursor.execute(cart_query)
            cart_data = cursor.fetchall()
            df_cart = pd.DataFrame(cart_data, columns=['user_id', 'product_id', 'cart_count'])
            df_cart['score'] = df_cart['cart_count'] * 2

            print(f"df_cart:\n {df_cart}")

            # Lấy dữ liệu từ bảng view_product (trọng số = 1)
            view_products_query = """
                SELECT user_id, product_id, COUNT(vp.product_id) AS vp_count
                FROM view_product vp
                JOIN product p ON vp.product_id = p.id
                WHERE vp.count > 5
                AND p.is_available = TRUE AND p.is_blocked = FALSE AND p.is_deleted = FALSE
                GROUP BY vp.user_id, vp.product_id;
            """
            cursor.execute(view_products_query)
            view_products_data = cursor.fetchall()
            df_view_products = pd.DataFrame(view_products_data, columns=['user_id', 'product_id', 'vp_count'])
            df_view_products['score'] = df_view_products['vp_count'] * 1

            print(f"df_view_products:\n {df_view_products}")

            cursor.close()
            connection.close()

            # Tổng hợp tất cả vào df_user_item
            df_user_item = pd.concat([
                df_order[['user_id', 'product_id', 'score']],
                df_followings[['user_id', 'product_id', 'score']],
                df_cart[['user_id', 'product_id', 'score']],
                df_view_products[['user_id', 'product_id', 'score']]
            ])

            df_user_item = df_user_item.groupby(['user_id', 'product_id'])['score'].sum().reset_index()

            return df_user_item

        except Exception as e:
            print(f"Lỗi lấy df_user_item: {str(e)}")
            return None

    def get_df_item(self):
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            product_query = """
                SELECT id, name, description, details, category_id, brand_id, store_id FROM product p
                WHERE p.is_available = true AND p.is_blocked = false AND p.is_deleted = false
            """
            category_query = "SELECT id, name FROM category c WHERE c.is_deleted = false"
            brand_query = "SELECT id, name FROM brand b WHERE b.is_deleted = false"
            store_query = """
                SELECT id, name FROM store s
                WHERE s.is_deleted = false AND s.is_banned = false
            """

            cursor.execute(product_query)
            product_data = cursor.fetchall()
            product_columns = [desc[0] for desc in cursor.description]

            cursor.execute(category_query)
            category_data = cursor.fetchall()
            category_columns = [desc[0] for desc in cursor.description]

            cursor.execute(brand_query)
            brand_data = cursor.fetchall()
            brand_columns = [desc[0] for desc in cursor.description]

            cursor.execute(store_query)
            store_data = cursor.fetchall()
            store_columns = [desc[0] for desc in cursor.description]

            cursor.close()
            connection.close()

            df_product = pd.DataFrame(product_data, columns=product_columns)
            df_category = pd.DataFrame(category_data, columns=category_columns)
            df_brand = pd.DataFrame(brand_data, columns=brand_columns)
            df_store = pd.DataFrame(store_data, columns=store_columns)

            df_product = df_product[["id", "name", "description", "details", "category_id", "brand_id", "store_id"]].rename(columns={"id": "product_id", "name": "product_name", "description": "product_description", "details": "product_details"})
            df_category = df_category[["id", "name"]].rename(columns={"id": "category_id", "name": "category_name"})
            df_brand = df_brand[["id", "name"]].rename(columns={"id": "brand_id", "name": "brand_name"})
            df_store = df_store[["id", "name"]].rename(columns={"id": "store_id", "name": "store_name"})

            df_item = df_product
            df_item = df_item.merge(df_category, on="category_id", how="left")
            df_item = df_item.merge(df_brand, on="brand_id", how="left")
            df_item = df_item.merge(df_store, on="store_id", how="left")

            df_item["item"] = (
                    df_item["product_name"].fillna("") + " " +
                    df_item["category_name"].fillna("") + " " +
                    df_item["brand_name"].fillna("") + " " +
                    df_item["store_name"].fillna("") + " " +
                    df_item["product_description"].fillna("") + " " +
                    df_item["product_details"].fillna("")
            )

            return df_item

        except Exception as e:
            print(f"Lỗi lấy df_item: {str(e)}")
            return None

    def get_response_list_product(self, list_product_id):
        if not list_product_id:
            return []
        
        try:
            connection = self.get_connection()
            if not connection:
                return []

            cursor = connection.cursor()

            product_query = """
                SELECT id, name, video_url, main_image_url, sale_price, original_price, sold, slug FROM product
                WHERE id = ANY(%s) AND is_available = TRUE AND is_blocked = FALSE AND is_deleted = FALSE
                ORDER BY array_position(%s, id)
            """
            cursor.execute(product_query, (list_product_id, list_product_id))
            products = cursor.fetchall()

            cursor.close()
            connection.close()

            listProduct = []
            for product in products:
                id, name, video_url, main_image_url, sale_price, original_price, sold, slug = product
                percent_discount = round(((original_price - sale_price) / original_price) * 100) if original_price > sale_price else 0

                listProduct.append({
                    "id": id,
                    "name": name,
                    "videoUrl": video_url,
                    "mainImageUrl": main_image_url,
                    "salePrice": float(sale_price),
                    "sold": sold,
                    "percentDiscount": percent_discount,
                    "slug": slug
                })

            return listProduct

        except Exception as e:
            print(f"Connect database fail: {str(e)}")
            return []