from datetime import datetime, timedelta
import pytest
from unittest.mock import Mock

# Importaciones simuladas del dominio y aplicación de NovaRent
from novarent.dominio.valores import LicenciaConducir, CategoriaVehiculo
from novarent.dominio.vehiculo import Vehiculo
from novarent.dominio.politicas_de_cargo import PoliticaDeCargo
from novarent.infraestructura.memoria import RepositorioVehiculosEnMemoria

class LicenciaVencidaError(Exception): pass
class SinVehiculosDisponiblesParaCompensacionError(Exception): pass

# --- PRUEBA DE PERSISTENCIA (Repositorio) ---
def test_persistencia_repositorio_vehiculos():
    repo = RepositorioVehiculosEnMemoria()
    vehiculo = Vehiculo(id="V-100", categoria=CategoriaVehiculo.COMPACTO, disponible=True)
    
    repo.guardar(vehiculo)
    recuperado = repo.obtener_por_id("V-100")
    
    assert recuperado is not None
    assert recuperado.id == "V-100"
    assert recuperado.disponible is True

# --- PRUEBA CON MOCK (Servicio Externo simulado de Pasarela de Pagos / Notificación) ---
def test_servicio_externo_notificacion_pago_mock():
    # Mock para un servicio de pasarela de pagos externo o pasarela antifraude
    pasarela_externa_mock = Mock()
    pasarela_externa_mock.procesar_cobro.return_value = {"status": "SUCCESS", "transaction_id": "TXN-998877"}
    
    resultado = pasarela_externa_mock.procesar_cobro(monto=1500.00, moneda="MXN")
    
    pasarela_externa_mock.procesar_cobro.assert_called_once_with(monto=1500.00, moneda="MXN")
    assert resultado["status"] == "SUCCESS"
    assert resultado["transaction_id"] == "TXN-998877"

# --- PRUEBA DE REGLA DE NEGOCIO RN-02 (Cargos por Retraso) ---
def test_rn02_calculo_cargo_por_retraso_limite():
    politica = PoliticaDeCargo(tarifa_hora_extra=150.0, minutos_gracia=30)
    
    # Caso límite: Retraso exacto de 30 minutos (dentro de gracia -> 0 cargo)
    cargo_dentro = politica.calcular_cargo(retraso=timedelta(minutes=30))
    assert cargo_dentro == 0.0

    # Caso error/retraso: Retraso de 4 horas
    cargo_tarde = politica.calcular_cargo(retraso=timedelta(hours=4))
    assert cargo_tarde == 600.0