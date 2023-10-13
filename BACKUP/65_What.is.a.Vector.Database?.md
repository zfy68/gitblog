# [What is a Vector Database?](https://github.com/zfy68/gitblog/issues/65)

### [What is a Vector Database?](https://www.pinecone.io/learn/vector-database/)

![image](https://user-images.githubusercontent.com/37278360/224461626-a6b141ab-8e9c-43bf-9b72-b013293c9186.png)



---

**Vector database，也叫矢量数据库，是一种专门用于存储和管理矢量数据的数据库系统。矢量数据是指通过点、线、面等几何对象来描述空间信息的数据，如地图、道路、建筑物、河流等。矢量数据库具有高效性和灵活性，能够处理大量的复杂空间数据，可用于地理信息系统（GIS）、遥感、测绘等领域。常见的矢量数据库系统有Oracle Spatial、PostGIS、Microsoft SQL Server、GeoJSON等。**


---

**矢量数据库索引和存储矢量嵌入以进行快速检索和相似性搜索，具有 CRUD 操作、元数据过滤和水平缩放等功能。**

---

### Why Use a Vector Database?

1. Semantic search
2. Similarity search for images, audio, video, JSON, and other forms of unstructured data
3. Ranking and recommendation engines
4. Deduplication and record matching
5. Anomaly detection

1.语义搜索
2. 图像、音频、视频、JSON等非结构化数据的相似度搜索
3. 排名和推荐引擎
4.去重和记录匹配
5.异常检测

---

### Required Capabilities of a Vector Database

1. Vector Indexes for Search and Retrieval
![image](https://user-images.githubusercontent.com/37278360/224462188-49c68c07-4790-435f-ac49-fa0a153bad2f.png)

3. Single-Stage Filtering
![image](https://user-images.githubusercontent.com/37278360/224462198-7a1bdcf5-8d7f-4c91-9b8a-7c6050787e91.png)

4. Data Sharding
![image](https://user-images.githubusercontent.com/37278360/224462206-cd5efd34-1a49-470e-ae67-75461fb3f0cd.png)

5. Replication
6. Hybrid Storage
7. API


### 矢量数据库所需的功能
1. 用于搜索和检索的向量索引
2. 单级过滤
3.数据分片
4.复制
5.混合存储
6. 应用程序接口

---

### Learn More about Vector Databases
Visit the [Pinecone learning center](https://www.pinecone.io/learn/) and read more about key concepts, including vector embeddings, vector indexes, and NLP for semantic search. Here are some of the most popular topics:

[Sentence Transformers: Meanings in Disguise](https://www.pinecone.io/learn/sentence-embeddings/) - This guide discusses core techniques for converting text and documents into vector embeddings and details some of the most popular NLP embedding models.

[The Missing WHERE Clause in Vector Search](https://www.pinecone.io/learn/vector-search-filtering/) - This article explains two common methods for adding metadata filters to vector search, and explores their limitations. Then, we cover how Single-Stage Filtering bridges some of these gaps.

[Nearest Neighbor Indexes for Similarity Search](https://www.pinecone.io/learn/vector-indexes/) - This article explores the pros and cons of some of the most important indexes including Flat, LSH, HNSW, and IVF. It also gives tips for deciding which to use and the impact of parameters in each index.



了解有关矢量数据库的更多信息
访问 Pinecone 学习中心并阅读有关关键概念的更多信息，包括矢量嵌入、矢量索引和用于语义搜索的 NLP。 以下是一些最热门的话题：

Sentence Transformers: Meanings in Disguise - 本指南讨论了将文本和文档转换为向量嵌入的核心技术，并详细介绍了一些最流行的 NLP 嵌入模型。

The Missing WHERE Clause in Vector Search - 本文解释了将元数据过滤器添加到矢量搜索的两种常用方法，并探讨了它们的局限性。 然后，我们将介绍单级过滤如何弥合其中的一些差距。

Nearest Neighbor Indexes for Similarity Search - 本文探讨了一些最重要的索引的优缺点，包括 Flat、LSH、HNSW 和 IVF。 它还提供了决定使用哪个以及每个索引中参数的影响的提示。

---

### Launch Your First Vector Database
Once you have your vector embeddings, you’ll need a vector database to index, store, and retrieve them.

[Create an account](https://app.pinecone.io/) and launch your first vector database.

With Pinecone, you can do this in just a few minutes. Pinecone is a fully managed vector database that makes it easy to add vector search to production applications. It combines vector search libraries, capabilities such as filtering, and distributed infrastructure to provide high performance and reliability at any scale.


启动您的第一个矢量数据库
一旦你有了向量嵌入，你就需要一个向量数据库来索引、存储和检索它们。

创建一个帐户并启动您的第一个矢量数据库。

使用 Pinecone，您只需几分钟即可完成此操作。 Pinecone 是一个完全托管的矢量数据库，可以轻松地将矢量搜索添加到生产应用程序中。 它结合了矢量搜索库、过滤等功能和分布式基础架构，可在任何规模下提供高性能和可靠性。