#!/usr/bin/env python3
"""
Script de teste rápido para verificar se a API está funcionando
Testa apenas endpoints básicos sem criar dados
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_quick_endpoints():
    """Teste rápido dos endpoints principais"""
    
    endpoints = [
        # Sistema
        ("GET", "/", "Página inicial"),
        ("GET", "/docs", "Swagger UI"),
        ("GET", "/system/health", "Health check"),
        
        # Debug
        ("GET", "/debug/routes", "Lista de rotas"),
        ("GET", "/debug/api-status", "Status da API"),
        
        # V2 Básicos
        ("GET", "/api/v2/test", "Endpoint de teste"),
        ("GET", "/api/v2/courses-simple", "Courses simples"),
        ("GET", "/api/v2/courses/courses", "Lista courses"),
        
        # Informativos
        ("GET", "/api/overview", "Overview da API"),
        ("GET", "/api/v2/tips/strategies", "Estratégias TIPS"),
        ("GET", "/api/v2/assessments/types", "Tipos de assessments")
    ]
    
    print("🚀 Teste Rápido IVO V2")
    print("=" * 50)
    
    results = []
    
    for method, endpoint, description in endpoints:
        try:
            start = datetime.now()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            duration = (datetime.now() - start).total_seconds() * 1000
            
            status = "✅" if 200 <= response.status_code < 300 else "❌"
            print(f"{status} {method} {endpoint} - {response.status_code} ({duration:.0f}ms)")
            print(f"    {description}")
            
            results.append({
                'endpoint': endpoint,
                'status': response.status_code,
                'success': 200 <= response.status_code < 300,
                'duration_ms': round(duration, 2)
            })
            
        except Exception as e:
            print(f"❌ {method} {endpoint} - ERROR")
            print(f"    Erro: {str(e)}")
            results.append({
                'endpoint': endpoint,
                'status': 0,
                'success': False,
                'error': str(e)
            })
    
    # Resumo
    total = len(results)
    success = len([r for r in results if r['success']])
    
    print("=" * 50)
    print(f"📊 Resultado: {success}/{total} sucessos ({success/total*100:.1f}%)")
    
    if success == total:
        print("🎉 Todos os testes básicos passaram!")
    else:
        print("⚠️ Alguns testes falharam. Execute o teste completo para detalhes:")
        print("python test_all_endpoints.py")

if __name__ == "__main__":
    test_quick_endpoints()