from rest_framework import serializers

class SampleSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        fields = ['title', 'description']
