from rest_framework import serializers

from shop.models import Seed, SeedMedia, SeedUser, SeedCart, SeedOrder


class SeedMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeedMedia
        fields = ['id', 'seed', 'start_day', 'end_day']

class SeedMediaGetSerializer(serializers.ModelSerializer):
    growing_img = serializers.ListField(child=serializers.CharField())
    class Meta(SeedMediaSerializer.Meta):
        fields = SeedMediaSerializer.Meta.fields + ['growing_img']

class SeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seed
        fields = '__all__'

class SeedCartSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='seed.name', read_only=True)
    seed_price = serializers.FloatField(source='seed.buy_price', read_only=True)
    cover_img = serializers.ImageField(source='seed.cover_img', read_only=True)
    class Meta:
        model = SeedCart
        fields = ['id', 'name', 'seed_price', 'cover_img', 'seed', 'user', 'purchased_amount', 'method_silica', 'method_botanicare', 'method_rhizo', 'payment_method', 'price_sum']

class SeedUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='seed.name', read_only=True)
    buy_price = serializers.FloatField(source='seed.buy_price', read_only=True)
    cover_img = serializers.ImageField(source='seed.cover_img', read_only=True)
    vegetation_mass_period = serializers.IntegerField(read_only=True)
    flowering_preharvest_period = serializers.IntegerField(read_only=True)
    harvest_period = serializers.IntegerField(source='seed.harvest_period', read_only=True)
    drying_period = serializers.IntegerField(source='seed.drying_period', read_only=True)
    curing_period = serializers.IntegerField(source='seed.curing_period', read_only=True)
    packing_period = serializers.IntegerField(source='seed.packing_period', read_only=True)
    harvest_rate = serializers.FloatField(source='seed.harvest_rate', read_only=True)
    current_period = serializers.IntegerField(read_only=True)
    warehouse_period = serializers.IntegerField(read_only=True)
    seed_media = SeedMediaGetSerializer(source='seed.seed_media', many=True, read_only=True)  # Include this line
    user_email = serializers.EmailField(read_only=True)
    class Meta:
        model = SeedUser
        fields = ['id', 'user_email', 'name', 'buy_price', 'cover_img', 'harvest_rate', 'vegetation_mass_period', 'flowering_preharvest_period', 'harvest_period', 'drying_period', 'curing_period', 'packing_period', 'seed', 'user', 'purchased_amount', 'profit', 'status', 'purchased_at', 'est_harvest_at', 'current_period', 'warehouse_period', 'seed_media', 'method_silica', 'method_botanicare', 'method_rhizo', 'payment_method', 'price_sum']

class SellOrderSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='seed.name', read_only=True)
    buy_price = serializers.FloatField(source='seed.buy_price', read_only=True)
    cover_img = serializers.ImageField(source='seed.cover_img', read_only=True)
    vegetation_mass_period = serializers.IntegerField(read_only=True)
    flowering_preharvest_period = serializers.IntegerField(read_only=True)
    harvest_period = serializers.IntegerField(source='seed.harvest_period', read_only=True)
    drying_period = serializers.IntegerField(source='seed.drying_period', read_only=True)
    curing_period = serializers.IntegerField(source='seed.curing_period', read_only=True)
    packing_period = serializers.IntegerField(source='seed.packing_period', read_only=True)
    harvest_rate = serializers.FloatField(source='seed.harvest_rate', read_only=True)
    purchased_amount = serializers.FloatField(source='purchase.purchased_amount', read_only=True)
    method_silica = serializers.FloatField(source='purchase.method_silica', read_only=True)
    method_botanicare = serializers.FloatField(source='purchase.method_botanicare', read_only=True)
    method_rhizo = serializers.FloatField(source='purchase.method_rhizo', read_only=True)
    payment_method= serializers.FloatField(source='purchase.payment_method', read_only=True)
    profit = serializers.FloatField(source='purchase.profit', read_only=True)
    total_period = serializers.IntegerField(read_only=True)
    total_purchase = serializers.FloatField(read_only=True) 
    total_profit = serializers.FloatField(read_only=True) 
    harvest_amount = serializers.FloatField(read_only=True) 
    user_email = serializers.EmailField(read_only=True)
    user_name = serializers.CharField(read_only=True)
    class Meta:
        model = SeedOrder
        fields = ['id', 'user_name', 'user_email', 'status', 'name', 'buy_price', 'cover_img', 'harvest_rate', 'vegetation_mass_period', 'flowering_preharvest_period', 'harvest_period', 'drying_period', 'curing_period', 'packing_period', 'seed', 'user', 'purchase', 'purchased_amount', 'profit', 'status', 'total_period', 'total_purchase', 'total_profit', 'harvest_amount', 'payment_method', 'method_silica', 'method_botanicare', 'method_rhizo']