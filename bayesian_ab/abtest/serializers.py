from rest_framework import serializers

class ABResponseSerializer(serializers.Serializer):

    campaign_code = serializers.CharField(max_length=36) 
    variant_code = serializers.CharField(max_length=32)
    register_impression = serializers.BooleanField()
    register_conversion = serializers.BooleanField()
    params = serializers.JSONField(required=False)


class SimPageVisitsSerializer(serializers.Serializer):

    campaign_code = serializers.CharField()
    conversion_rates = serializers.JSONField(required=False)
    n = serializers.IntegerField(min_value=1, max_value=100)
    algo = serializers.CharField(max_length=64)

class SimulationSerializer(serializers.Serializer):

    # Serializer for SimulationSerializer
    p1 = serializers.FloatField(min_value=0.01, max_value=0.99)
    p2 = serializers.FloatField(min_value=0.01, max_value=0.99)
    p3 = serializers.FloatField(min_value=0.01, max_value=0.99)
    algo = serializers.CharField(max_length=64)
    eps = serializers.FloatField(min_value=0.01, max_value=0.99, required=False)

