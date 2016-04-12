from py2neo import Graph, Node, Relationship, authenticate
from passlib.hash import bcrypt
from datetime import datetime
import time
import uuid
authenticate("localhost:7474", "neo4j", "")
graph = Graph()


class User:
	def __init__(self,username):
		self.username = username

	def find(self):
		user = graph.find_one("User","username",self.username)
		return user

	def register(self,password):
		if not self.find():
			user = Node("User", username = self.username, password = bcrypt.encrypt(password))
			graph.create(user)
			return True
		else: return False

	def verify_pass(self,password):
		user = self.find()
		if not user:
			return False
		else: 
			return bcrypt.verify(password, user["password"])

	def add_post(self, title,tags,text):
		user = self.find()

		post = Node(
			"Post",
			id=str(uuid.uuid4()),
			title=title,
			text=text,
			timestamp = int(time.time()),
			date=datetime.now().strftime("%Y-%m-%d")
			)

		rel = Relationship(user, "PUBLISHED", post)
		graph.create(rel)

		tags = set([x.strip() for x in tags.lower().split(",")])

		for tag in tags:
			t = graph.merge_one("Tag", "name", tag)
			rel = Relationship(t, "TAGGED", post)
			graph.create(rel)

	def like(self,post_id):
		user = self.find()
		post = graph.find_one("Post","id",post_id)
		graph.create_unique(Relationship(user,"LIKES",post))

	def my_own_posts(self,n):
		query = """MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
		WHERE user.username={username}
		RETURN post, COLLECT(tag.name) AS tags ORDER BY post.timestamp DESC LIMIT {n}"""
		#today = datetime.now().strftime("%Y-%m-%d")
		#today = "2016-04-10"
		username = self.username
		return graph.cypher.execute(query, username = username,n=n)

	def similar_users(self,n):
		query = """MATCH (user1:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
		(user2:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag) WHERE user1.username = {username} AND user1 <> user2
		WITH user2, COLLECT(DISTINCT tag.name) AS tags, COUNT(DISTINCT tag.name) AS tag_count
		ORDER BY tag_count DESC LIMIT {n}
		RETURN user2.username AS similar_user, tags"""
		return graph.cypher.execute(query, username = self.username, n=n)

	def commonality(self, user):
		query1=""" MATCH (user1:User)-[:PUBLISHED]->(post:Post)<-[:LIKES]-(user2:User)
		WHERE user1.username = {username1} AND user2.username = {username2}
		RETURN COUNT(post) AS likes"""

		likes = graph.cypher.execute(query1, username1=self.username, username2 = user.username)[0]["likes"]
		likes = 0 if not likes else likes

		query2 = """ MATCH (user1:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag),
		(user2:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
		WHERE user1.username = {username1} AND user2.username = {username2}
		RETURN COLLECT(DISTINCT tag.name) AS tags"""

		tags = graph.cypher.execute(query2, username1 = self.username, username2 = user.username)[0]["tags"]
		return {"likes": likes, "tags": tags}


def todays_recent_posts(n):
	query = """MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
	WHERE post.timestamp <= {today}
	RETURN user.username, post, COLLECT(tag.name) AS tags ORDER BY post.timestamp DESC LIMIT {n}"""
	#today = datetime.now().strftime("%Y-%m-%d")
	#today = "2016-04-10"
	today = int(time.time())
	return graph.cypher.execute(query, today=today,n=n)

