#!/usr/bin/env python3
"""
Простой тест мониторинга без эмодзи для Windows
"""

import asyncio
import json
import logging
import sys
import time

import aiohttp

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SimpleMonitoringTest:
    """Простой тестер мониторинга."""

    def __init__(self):
        self.netdata_url = "http://localhost:19999"
        self.uptime_kuma_url = "http://localhost:3001"
        self.timeout = 10
        self.results = {"netdata": {}, "uptime_kuma": {}, "summary": {}}

    async def test_netdata(self):
        """Тест Netdata."""
        logger.info("Тестируем Netdata...")

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # Проверка главной страницы
                async with session.get(f"{self.netdata_url}/") as response:
                    if response.status == 200:
                        self.results["netdata"]["web_available"] = True
                        logger.info("Netdata веб-интерфейс доступен")
                    else:
                        self.results["netdata"]["web_available"] = False
                        logger.warning(f"Netdata вернул статус {response.status}")

                # Проверка API
                try:
                    async with session.get(f"{self.netdata_url}/api/v1/info") as api_response:
                        if api_response.status == 200:
                            info_data = await api_response.json()
                            self.results["netdata"]["api_available"] = True
                            self.results["netdata"]["version"] = info_data.get("version", "unknown")
                            logger.info(f"Netdata API работает (версия: {info_data.get('version', 'unknown')})")
                        else:
                            self.results["netdata"]["api_available"] = False
                            logger.warning(f"Netdata API вернул статус {api_response.status}")
                except Exception as e:
                    self.results["netdata"]["api_available"] = False
                    logger.warning(f"Ошибка API Netdata: {e}")

        except asyncio.TimeoutError:
            self.results["netdata"]["web_available"] = False
            self.results["netdata"]["api_available"] = False
            logger.error("Netdata недоступен (таймаут)")
        except Exception as e:
            self.results["netdata"]["web_available"] = False
            self.results["netdata"]["api_available"] = False
            logger.error(f"Ошибка подключения к Netdata: {e}")

    async def test_uptime_kuma(self):
        """Тест Uptime Kuma."""
        logger.info("Тестируем Uptime Kuma...")

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # Проверка главной страницы
                async with session.get(f"{self.uptime_kuma_url}/") as response:
                    if response.status == 200:
                        self.results["uptime_kuma"]["web_available"] = True
                        logger.info("Uptime Kuma веб-интерфейс доступен")
                    else:
                        self.results["uptime_kuma"]["web_available"] = False
                        logger.warning(f"Uptime Kuma вернул статус {response.status}")

        except asyncio.TimeoutError:
            self.results["uptime_kuma"]["web_available"] = False
            logger.error("Uptime Kuma недоступен (таймаут)")
        except Exception as e:
            self.results["uptime_kuma"]["web_available"] = False
            logger.error(f"Ошибка подключения к Uptime Kuma: {e}")

    def generate_summary(self):
        """Генерация итогового отчета."""
        logger.info("Генерируем итоговый отчет...")

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
        }

    def print_report(self):
        """Вывод отчета в консоль."""
        print("\n" + "=" * 60)
        print("ОТЧЕТ О ТЕСТИРОВАНИИ МОНИТОРИНГА")
        print("=" * 60)

        # Общий статус
        overall = self.results["summary"]["overall_status"]
        print(f"\nОБЩИЙ СТАТУС: {overall}")

        # Netdata
        netdata_status = self.results["summary"]["netdata_status"]
        print(f"\nNETDATA: {netdata_status}")
        if self.results["netdata"].get("web_available"):
            print(f"   Веб-интерфейс: http://localhost:19999")
        if self.results["netdata"].get("version"):
            print(f"   Версия: {self.results['netdata']['version']}")

        # Uptime Kuma
        uptime_status = self.results["summary"]["uptime_kuma_status"]
        print(f"\nUPTIME KUMA: {uptime_status}")
        if self.results["uptime_kuma"].get("web_available"):
            print(f"   Веб-интерфейс: http://localhost:3001")

        print("\n" + "=" * 60)

    async def run_all_tests(self):
        """Запуск всех тестов."""
        logger.info("Запускаем тестирование мониторинга...")

        start_time = time.time()

        # Асинхронные тесты
        await asyncio.gather(self.test_netdata(), self.test_uptime_kuma())

        # Генерация отчета
        self.generate_summary()

        end_time = time.time()
        logger.info(f"Тестирование завершено за {end_time - start_time:.2f} секунд")

        return self.results

    def save_results(self, filename="monitoring_test_results.json"):
        """Сохранение результатов в файл."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            logger.info(f"Результаты сохранены в {filename}")
        except Exception as e:
            logger.error(f"Ошибка сохранения результатов: {e}")


async def main():
    """Главная функция."""
    print("ПРОСТОЙ ТЕСТ МОНИТОРИНГА")
    print("Проверяет доступность Netdata и Uptime Kuma")
    print("-" * 50)

    tester = SimpleMonitoringTest()

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
            print("\nВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            return 0
        elif overall_status == "PARTIAL":
            print("\nТЕСТЫ ПРОШЛИ ЧАСТИЧНО")
            return 1
        else:
            print("\nТЕСТЫ ПРОВАЛИЛИСЬ")
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
