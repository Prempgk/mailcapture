from rest_framework import serializers
from .models import *


class InputSerializer(serializers.Serializer):
    username = serializers.EmailField(allow_null=False, allow_blank=False)
    password = serializers.CharField(max_length=16, min_length=16, allow_blank=False, allow_null=False)


class MailDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailDetails
        fields = '__all__'
