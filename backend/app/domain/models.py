import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Time, Boolean
from sqlalchemy.orm import relationship
from app.infrastructure.database import Base 
from app.core.config import get_wib_time
from datetime import datetime

# TABEL USERS
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_wib_time)
    updated_at = Column(DateTime(timezone=True), default=get_wib_time, onupdate=get_wib_time)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relasi
    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan")


# TABEL DEVICES
class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    device_name = Column(String, unique=True, index=True)
    status_active = Column(Boolean, default=True)
    device_token = Column(String, unique=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_wib_time)
    updated_at = Column(DateTime(timezone=True), default=get_wib_time, onupdate=get_wib_time)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relasi
    owner = relationship("User", back_populates="devices")
    sensor_mq135_logs = relationship("SensorMQ135", back_populates="device", cascade="all, delete-orphan")
    sensor_dht22_logs = relationship("SensorDHT22", back_populates="device", cascade="all, delete-orphan")


# TABEL SENSOR_MQ135
class SensorMQ135(Base):
    __tablename__ = "sensor_mq135"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    mq135 = Column(Float)
    ppm_nh3 = Column(Float)
    ppm_co = Column(Float)
    ppm_co2 = Column(Float)
    ppm_acetone = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_wib_time)
    updated_at = Column(DateTime(timezone=True), default=get_wib_time, onupdate=get_wib_time)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relasi
    device = relationship("Device", back_populates="sensor_mq135_logs")
    conclusion_features = relationship("ConclusionFeature", back_populates="sensor_mq135", cascade="all, delete-orphan")


# TABEL SENSOR_DHT22
class SensorDHT22(Base):
    __tablename__ = "sensor_dht22"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    temperature = Column(Float)
    humidity = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_wib_time)
    updated_at = Column(DateTime(timezone=True), default=get_wib_time, onupdate=get_wib_time)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relasi
    device = relationship("Device", back_populates="sensor_dht22_logs")
    conclusion_features = relationship("ConclusionFeature", back_populates="sensor_dht22", cascade="all, delete-orphan")


# TABEL CONCLUSION_FEATURE
class ConclusionFeature(Base):
    __tablename__ = "conclusion_feature"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_mq135_id = Column(Integer, ForeignKey("sensor_mq135.id", ondelete="CASCADE"))
    sensor_dht22_id = Column(Integer, ForeignKey("sensor_dht22.id", ondelete="CASCADE"))
    hour = Column(Time)
    is_weekend = Column(Boolean)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_wib_time)
    updated_at = Column(DateTime(timezone=True), default=get_wib_time, onupdate=get_wib_time)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relasi ke Sensor
    sensor_mq135 = relationship("SensorMQ135", back_populates="conclusion_features")
    sensor_dht22 = relationship("SensorDHT22", back_populates="conclusion_features")
    
    # Relasi ke Classification dan Predictions
    classifications = relationship("Classification", back_populates="conclusion_feature", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="conclusion_feature", cascade="all, delete-orphan")

# TABEL CLASSIFICATION
class Classification(Base):
    __tablename__ = "classification"
    
    id = Column(Integer, primary_key=True, index=True)
    conclusion_feature_id = Column(Integer, ForeignKey("conclusion_feature.id", ondelete="CASCADE"))
    label_status = Column(String)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_wib_time)
    updated_at = Column(DateTime(timezone=True), default=get_wib_time, onupdate=get_wib_time)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relasi
    conclusion_feature = relationship("ConclusionFeature", back_populates="classifications")


# TABEL PREDICTIONS
class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    conclusion_feature_id = Column(Integer, ForeignKey("conclusion_feature.id", ondelete="CASCADE"))
    label_status = Column(String)
    target_time = Column(Time)
    target_date = Column(Date)
    confidence = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_wib_time)
    updated_at = Column(DateTime(timezone=True), default=get_wib_time, onupdate=get_wib_time)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relasi
    conclusion_feature = relationship("ConclusionFeature", back_populates="predictions")

class LogTesting(Base):
    __tablename__ = "log_testing"

    id = Column(Integer, primary_key=True, index=True)
    classification_id = Column(Integer, ForeignKey("classification.id", ondelete="CASCADE"))
    mode = Column(String)
    t_sensor = Column(Float)
    t_send = Column(Float)
    t_ack = Column(Float)
    t_actuator = Column(Float)
    rtt_us = Column(Float)
    e2e_us = Column(Float)
    payload_bits = Column(Float)
    payload_length = Column(Float)
    total_heap = Column(Float)
    free_heap = Column(Float)
    ram_load_pct = Column(Float)
    voltage_v = Column(Float)
    current_ma = Column(Float)
    power_mw = Column(Float)
    energy_mj = Column(Float)
    actuator_status = Column(String)
    created_at = Column(DateTime(timezone=True), default=get_wib_time)

    classification = relationship("Classification", backref="log_testing")