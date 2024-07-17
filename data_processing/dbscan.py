from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import numpy as np
from ...models import UserPreference
from processing import data_wrangling


df, books_df, reviews_df, users_df, reactions_df = data_wrangling()

def clust_df():
    encoder = OneHotEncoder()
    categorical_features = encoder.fit_transform(df[['genre', 'tags']]).toarray()

    scaler = StandardScaler()
    numerical_features = scaler.fit_transform(df[['rating', 'price']])

    features = np.concatenate((numerical_features, categorical_features), axis=1)

    dbscan = DBSCAN(eps=0.5, min_samples=50)
    clusters = dbscan.fit_predict(features)

    df['cluster_label'] = clusters

    for index, row in df.iterrows():
        try:
            user_pref = UserPreference.objects.get(name=row['name'])
            user_pref.cluster_label = row['cluster_label']
            user_pref.save()
        except UserPreference.DoesNotExist:
            continue



# unique_labels = np.unique(clusters)
# num_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
# print(f"Количество кластеров: {num_clusters}")  // 19

# print('silhouette score:', silhouette_score(features, clusters)) // -0.16 перекрывающиеся кластеры
# print('Davies-Bouldin Index:', davies_bouldin_score(features, clusters)) // 1.39
# print('Calinski-Harabasz Index:', calinski_harabasz_score(features, clusters)) // 86.52
