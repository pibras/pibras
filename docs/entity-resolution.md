# Entity Resolution

## Ordem canônica

```txt
1. Building
2. Unit
3. Property
4. Listing
```

`Unit` é a âncora de deduplicação. `Property` representa ciclo comercial e pode se repetir ao longo do tempo para a mesma unidade física.

## Campos de apoio em Unit

- `dedupe_key`;
- `normalized_address_key`;
- `area_signature`;
- `duplicate_of_unit_id`;
- `dedupe_confidence`;
- `dedupe_review_state`.

## Thresholds v0.2

```txt
auto_match_threshold: >= 0.95
manual_review_band: >= 0.75 e < 0.95
confirmed_unique_threshold: < 0.75
```

Merge errado é mais caro que duplicata temporária. Casos duvidosos devem ir para revisão humana.
