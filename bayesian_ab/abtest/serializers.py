from rest_framework import serializers

class ABResponseSerializer(serializers.Serializer):

    campaign_code = serializers.CharField() 
    variant_code = serializers.CharField()
    register_impression = serializers.BooleanField()
    register_conversion = serializers.BooleanField()
    params = serializers.JSONField(required=False)

# class OrderIDSerializer(serializers.Serializer):

#     order_id = serializers.IntegerField()

# class EmailSerializer(serializers.Serializer):

#     email = serializers.EmailField()

# class UserPermissionSerializer(serializers.Serializer):

#     user_id = serializers.IntegerField()
#     perm_id = serializers.IntegerField()

# class OrderDocumentSerializer(serializers.Serializer):

#     order_id = serializers.IntegerField()
#     do_id = serializers.IntegerField(required=False, allow_null=True)
#     inv_id = serializers.IntegerField(required=False, allow_null=True)
#     cn_id = serializers.IntegerField(required=False, allow_null=True)


# class SearchUserSerializer(serializers.Serializer):

#     # Search field for users

#     search = serializers.CharField(allow_null=True, allow_blank=True)
#     page = serializers.IntegerField()