                # try:
                #     limit_int = int(limit) if limit is not None else 0
                #     if limit_int > 0:
                #         if not query.endswith('\n'):
                #             query = query + '\n'
                #         query = query + f"LIMIT {limit_int}\n"
                # except Exception:
                #     logger.warning(f"無効な limit 指定を無視します: {limit}")