#!/usr/bin/env python3
"""
Легковесный тест мониторинга для слабых VPS
Проверяет доступность Netdata и Uptime Kuma без нагрузки на сервер
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

import aiohttp

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class LightweightMonitoringTest:
    """Легковесный тестер мониторинга."""

    def __init__(self):
        self.netdata_url = "http://localhost:19999"
        self.uptime_kuma_url = "http://localhost:3001"
        self.timeout = 10  # Короткий таймаут для слабых VPS
        self.results = {"netdata": {}, "uptime_kuma": {}, "summary": {}}

    async def test_netdata_availability(self):
        """Тест доступности Netdata."""
        logger.info("🔍 Тестируем доступность Netdata...")

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # Простая проверка главной страницы
                async with session.get(f"{self.netdata_url}/") as response:
                    if response.status == 200:
                        self.results["netdata"]["web_available"] = True
                        logger.info("✅ Netdata веб-интерфейс доступен")
                    else:
                        self.results["netdata"]["web_available"] = False
                        logger.warning(f"⚠️ Netdata вернул статус {response.status}")

                # Проверка API (легковесный endpoint)
                try:
                    async with session.get(f"{self.netdata_url}/api/v1/info") as api_response:
                        if api_response.status == 200:
                            info_data = await api_response.json()
                            self.results["netdata"]["api_available"] = True
                            self.results["netdata"]["version"] = info_data.get("version", "unknown")
                            self.results["netdata"]["hostname"] = info_data.get("hostname", "unknown")
                            logger.info(f"✅ Netdata API работает (версия: {info_data.get('version', 'unknown')})")
                        else:
                            self.results["netdata"]["api_available"] = False
                            logger.warning(f"⚠️ Netdata API вернул статус {api_response.status}")
                except Exception as e:
                    self.results["netdata"]["api_available"] = False
                    logger.warning(f"⚠️ Ошибка API Netdata: {e}")

        except asyncio.TimeoutError:
            self.results["netdata"]["web_available"] = False
            self.results["netdata"]["api_available"] = False
            logger.error("❌ Netdata недоступен (таймаут)")
        except Exception as e:
            self.results["netdata"]["web_available"] = False
            self.results["netdata"]["api_available"] = False
            logger.error(f"❌ Ошибка подключения к Netdata: {e}")

    async def test_uptime_kuma_availability(self):
        """Тест доступности Uptime Kuma."""
        logger.info("🔍 Тестируем доступность Uptime Kuma...")

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # Простая проверка главной страницы
                async with session.get(f"{self.uptime_kuma_url}/") as response:
                    if response.status == 200:
                        self.results["uptime_kuma"]["web_available"] = True
                        logger.info("✅ Uptime Kuma веб-интерфейс доступен")
                    else:
                        self.results["uptime_kuma"]["web_available"] = False
                        logger.warning(f"⚠️ Uptime Kuma вернул статус {response.status}")

                # Проверка статуса (без авторизации)
                try:
                    async with session.get(f"{self.uptime_kuma_url}/api/status-page/heartbeat") as status_response:
                        if status_response.status in [200, 401]:  # 401 = нужна авторизация, но сервис работает
                            self.results["uptime_kuma"]["api_responding"] = True
                            logger.info("✅ Uptime Kuma API отвечает")
                        else:
                            self.results["uptime_kuma"]["api_responding"] = False
                            logger.warning(f"⚠️ Uptime Kuma API статус: {status_response.status}")
                except Exception as e:
                    self.results["uptime_kuma"]["api_responding"] = False
                    logger.warning(f"⚠️ Ошибка API Uptime Kuma: {e}")

        except asyncio.TimeoutError:
            self.results["uptime_kuma"]["web_available"] = False
            self.results["uptime_kuma"]["api_responding"] = False
            logger.error("❌ Uptime Kuma недоступен (таймаут)")
        except Exception as e:
            self.results["uptime_kuma"]["web_available"] = False
            self.results["uptime_kuma"]["api_responding"] = False
            logger.error(f"❌ Ошибка подключения к Uptime Kuma: {e}")

    async def test_system_resources_light(self):
        """Легкая проверка системных ресурсов через Netdata."""
        logger.info("🔍 Проверяем системные ресурсы (легкий режим)...")

        if not self.results["netdata"].get("api_available"):
            logger.warning("⚠️ Netdata API недоступен, пропускаем проверку ресурсов")
            return

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # Получаем только основные метрики CPU и RAM
                endpoints = {
                    "cpu": "/api/v1/data?chart=system.cpu&after=-60&points=1&group=average&format=json",
                    "ram": "/api/v1/data?chart=system.ram&after=-60&points=1&group=average&format=json",
                }

                for metric_name, endpoint in endpoints.items():
                    try:
                        async with session.get(f"{self.netdata_url}{endpoint}") as response:
                            if response.status == 200:
                                data = await response.json()
                                if data and "data" in data and len(data["data"]) > 0:
                                    self.results["netdata"][f"{metric_name}_data"] = data["data"][0]
                                    logger.info(f"✅ Получены данные {metric_name}")
                                else:
                                    logger.warning(f"⚠️ Пустые данные для {metric_name}")
                            else:
                                logger.warning(f"⚠️ Ошибка получения {metric_name}: {response.status}")
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка метрики {metric_name}: {e}")

        except Exception as e:
            logger.error(f"❌ Ошибка проверки ресурсов: {e}")

    def check_docker_containers(self):
        """Проверка Docker контейнеров (если используется Docker)."""
        logger.info("🔍 Проверяем Docker контейнеры...")

        try:
            import subprocess

            # Проверяем, есть ли Docker
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}", "--filter", "name=netdata"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and "netdata" in result.stdout:
                self.results["netdata"]["docker_running"] = True
                logger.info("✅ Docker контейнер Netdata запущен")
            else:
                self.results["netdata"]["docker_running"] = False
                logger.info("ℹ️ Docker контейнер Netdata не найден (возможно, используется systemd)")

            # Проверяем Uptime Kuma
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}", "--filter", "name=uptime-kuma"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and "uptime-kuma" in result.stdout:
                self.results["uptime_kuma"]["docker_running"] = True
                logger.info("✅ Docker контейнер Uptime Kuma запущен")
            else:
                self.results["uptime_kuma"]["docker_running"] = False
                logger.info("ℹ️ Docker контейнер Uptime Kuma не найден (возможно, используется systemd)")

        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Таймаут проверки Docker контейнеров")
        except FileNotFoundError:
            logger.info("ℹ️ Docker не установлен или недоступен")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка проверки Docker: {e}")

    def check_systemd_services(self):
        """Проверка systemd сервисов."""
        logger.info("🔍 Проверяем systemd сервисы...")

        try:
            import subprocess

            services = ["netdata", "uptime-kuma"]

            for service in services:
                try:
                    result = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True, timeout=3)

                    if result.returncode == 0 and result.stdout.strip() == "active":
                        self.results[service.replace("-", "_")]["systemd_active"] = True
                        logger.info(f"✅ Systemd сервис {service} активен")
                    else:
                        self.results[service.replace("-", "_")]["systemd_active"] = False
                        logger.info(f"ℹ️ Systemd сервис {service} неактивен")

                except subprocess.TimeoutExpired:
                    logger.warning(f"⚠️ Таймаут проверки сервиса {service}")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка проверки сервиса {service}: {e}")

        except FileNotFoundError:
            logger.info("ℹ️ systemctl недоступен")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка проверки systemd: {e}")

    def generate_summary(self):
        """Генерация итогового отчета."""
        logger.info("📊 Генерируем итоговый отчет...")

        # Netdata статус
        netdata_ok = self.results["netdata"].get("web_available", False) and self.results["netdata"].get(
            "api_available", False
        )

        # Uptime Kuma статус
        uptime_kuma_ok = self.results["uptime_kuma"].get("web_available", False)

        self.results["summary"] = {
            "netdata_status": "OK" if netdata_ok else "FAIL",
            "uptime_kuma_status": "OK" if uptime_kuma_ok else "FAIL",
            "overall_status": (
                "OK" if (netdata_ok and uptime_kuma_ok) else "PARTIAL" if (netdata_ok or uptime_kuma_ok) else "FAIL"
            ),
            "test_timestamp": int(time.time()),
            "recommendations": [],
        }

        # Рекомендации
        if not netdata_ok:
            self.results["summary"]["recommendations"].append(
                "Проверьте статус Netdata: systemctl status netdata или docker ps"
            )

        if not uptime_kuma_ok:
            self.results["summary"]["recommendations"].append(
                "Проверьте статус Uptime Kuma: systemctl status uptime-kuma или docker ps"
            )

        if netdata_ok and uptime_kuma_ok:
            self.results["summary"]["recommendations"].append(
                "Мониторинг работает корректно! Настройте алерты в веб-интерфейсах."
            )

    def print_report(self):
        """Вывод отчета в консоль."""
        print("\n" + "=" * 60)
        print("📊 ОТЧЕТ О ТЕСТИРОВАНИИ МОНИТОРИНГА")
        print("=" * 60)

        # Общий статус
        overall = self.results["summary"]["overall_status"]
        status_emoji = {"OK": "✅", "PARTIAL": "⚠️", "FAIL": "❌"}
        print(f"\n🎯 ОБЩИЙ СТАТУС: {status_emoji.get(overall, '❓')} {overall}")

        # Netdata
        netdata_status = self.results["summary"]["netdata_status"]
        print(f"\n🔹 NETDATA: {status_emoji.get(netdata_status, '❓')} {netdata_status}")
        if self.results["netdata"].get("web_available"):
            print(f"   📡 Веб-интерфейс: http://localhost:19999")
        if self.results["netdata"].get("version"):
            print(f"   📦 Версия: {self.results['netdata']['version']}")

        # Uptime Kuma
        uptime_status = self.results["summary"]["uptime_kuma_status"]
        print(f"\n🔹 UPTIME KUMA: {status_emoji.get(uptime_status, '❓')} {uptime_status}")
        if self.results["uptime_kuma"].get("web_available"):
            print(f"   📡 Веб-интерфейс: http://localhost:3001")

        # Рекомендации
        if self.results["summary"]["recommendations"]:
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            for i, rec in enumerate(self.results["summary"]["recommendations"], 1):
                print(f"   {i}. {rec}")

        print("\n" + "=" * 60)

    async def run_all_tests(self):
        """Запуск всех тестов."""
        logger.info("🚀 Запускаем легковесное тестирование мониторинга...")

        start_time = time.time()

        # Асинхронные тесты
        await asyncio.gather(
            self.test_netdata_availability(), self.test_uptime_kuma_availability(), self.test_system_resources_light()
        )

        # Синхронные проверки
        self.check_docker_containers()
        self.check_systemd_services()

        # Генерация отчета
        self.generate_summary()

        end_time = time.time()
        logger.info(f"⏱️ Тестирование завершено за {end_time - start_time:.2f} секунд")

        return self.results

    def save_results(self, filename="monitoring_test_results.json"):
        """Сохранение результатов в файл."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Результаты сохранены в {filename}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения результатов: {e}")


async def main():
    """Главная функция."""
    print("ЛЕГКОВЕСНЫЙ ТЕСТ МОНИТОРИНГА")
    print("Оптимизирован для слабых VPS серверов")
    print("-" * 50)

    tester = LightweightMonitoringTest()

    try:
        # Запускаем тесты
        results = await tester.run_all_tests()

        # Выводим отчет
        tester.print_report()

        # Сохраняем результаты
        tester.save_results()

        # Возвращаем код выхода
        overall_status = results["summary"]["overall_status"]
        if overall_status == "OK":
            return 0
        elif overall_status == "PARTIAL":
            return 1
        else:
            return 2

    except KeyboardInterrupt:
        logger.info("Тестирование прервано пользователем")
        return 130
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"Фатальная ошибка: {e}")
        sys.exit(1)
