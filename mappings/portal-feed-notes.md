# Portal feed notes

Feeds de portal são saída de distribuição, não modelo canônico.

## Fluxo

```txt
Property + Unit + Listing + MediaAsset
-> ExposurePolicy
-> PortalFeedMapper
-> PortalFeedValidator
-> PublicationLog
```

## Regras

- aplicar `ExposurePolicy` antes de exportar;
- validar XML/payload antes do envio;
- registrar o que foi enviado;
- não vazar proprietário, endereço completo, preço mínimo ou documentos;
- quando `price_display` for `on_request`, não emitir preço numérico; emitir apenas a política de exibição;
- preservar `external_ids[]` como fonte dos códigos por canal.
