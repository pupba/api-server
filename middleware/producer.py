from kafka import KafkaProducer, KafkaAdminClient
import json
se = json.loads(open('./secret1.json').read())


class MessageProducer:
    topic = ""
    producer = None

    def __init__(self, topic):
        self.broker = se.get('BROKER')
        self.topic = topic
        self.producer = KafkaProducer(bootstrap_servers=self.broker,
                                      value_serializer=lambda x: json.dumps(
                                          x).encode('utf-8'),
                                      acks=0,
                                      api_version=(2, 5, 0),
                                      retries=3)
        self.__client = KafkaAdminClient(bootstrap_servers=self.broker)

    def getTopicList(self):
        for i in self.__client.list_topics():
            print(i)

    def send_message(self, msg):
        try:
            future = self.producer.send(self.topic, msg)
            self.producer.flush()   # 비우는 작업
            future.get(timeout=60)
            return {'status_code': 200, 'error': None}
        except Exception as e:
            print("error:::::", e)
            return e
