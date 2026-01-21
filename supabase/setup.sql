-- ============================================================================
-- AI-POWERED SUPPORT CO-PILOT - DATABASE SCHEMA
-- ============================================================================
-- Este script configura la base de datos completa para el sistema de tickets
-- con soporte para análisis de IA, métricas y seguridad RLS
-- ============================================================================

-- Limpiar tablas existentes si existen (solo para desarrollo)
DROP TABLE IF EXISTS tickets CASCADE;
DROP TYPE IF EXISTS ticket_category CASCADE;
DROP TYPE IF EXISTS sentiment_type CASCADE;

-- ============================================================================
-- TIPOS ENUMERADOS
-- ============================================================================

-- Categorías de tickets basadas en los requerimientos
CREATE TYPE ticket_category AS ENUM (
    'Técnico',
    'Facturación', 
    'Comercial',
    'Otro'
);

-- Tipos de sentimiento para análisis emocional
CREATE TYPE sentiment_type AS ENUM (
    'Positivo',
    'Neutral',
    'Negativo'
);

-- ============================================================================
-- TABLA PRINCIPAL: TICKETS
-- ============================================================================

CREATE TABLE tickets (
    -- Identificadores y timestamps
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    -- Contenido del ticket
    description TEXT NOT NULL CHECK (char_length(description) >= 10),
    
    -- Resultados del análisis de IA
    category ticket_category,
    sentiment sentiment_type,
    
    -- Estado de procesamiento
    processed BOOLEAN NOT NULL DEFAULT false,
    
    -- Métricas adicionales (PLUS para destacar)
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    processing_time_ms INTEGER CHECK (processing_time_ms >= 0),
    
    -- Metadatos adicionales para análisis
    reasoning TEXT, -- Explicación del modelo sobre su clasificación
    model_version TEXT DEFAULT 'gpt-3.5-turbo' -- Para tracking de modelos
);

-- ============================================================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================================================

-- Índice para filtrar tickets no procesados (usado por n8n)
CREATE INDEX idx_tickets_processed ON tickets(processed) WHERE processed = false;

-- Índice para ordenar por fecha (usado por el dashboard)
CREATE INDEX idx_tickets_created_at ON tickets(created_at DESC);

-- Índice compuesto para análisis por sentimiento y categoría
CREATE INDEX idx_tickets_sentiment_category ON tickets(sentiment, category) WHERE processed = true;

-- Índice para búsqueda de texto (opcional, para futuras mejoras)
CREATE INDEX idx_tickets_description_gin ON tickets USING gin(to_tsvector('spanish', description));

-- ============================================================================
-- TRIGGER PARA ACTUALIZAR updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Habilitar RLS en la tabla
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;

-- Policy 1: Permitir SELECT a cualquier usuario (autenticado o anónimo)
-- Esto permite que el dashboard público pueda leer los tickets
CREATE POLICY "tickets_select_policy"
    ON tickets
    FOR SELECT
    USING (true);

-- Policy 2: Permitir INSERT a cualquier usuario
-- Esto permite crear tickets desde el formulario público
CREATE POLICY "tickets_insert_policy"
    ON tickets
    FOR INSERT
    WITH CHECK (true);

-- Policy 3: Permitir UPDATE solo a service_role
-- Solo la API de Python (usando service_role key) puede actualizar tickets
CREATE POLICY "tickets_update_policy"
    ON tickets
    FOR UPDATE
    USING (auth.jwt()->>'role' = 'service_role');

-- Policy 4: Prevenir DELETE (opcional, para seguridad)
-- Nadie puede eliminar tickets una vez creados
CREATE POLICY "tickets_delete_policy"
    ON tickets
    FOR DELETE
    USING (false);

-- ============================================================================
-- DATOS DE PRUEBA
-- ============================================================================

INSERT INTO tickets (description, processed) VALUES
    ('Mi aplicación se cierra cada vez que intento exportar el reporte mensual. Ya reinicié pero sigue fallando.', false),
    ('¡Excelente atención! El equipo resolvió mi problema en menos de 10 minutos. Muy satisfecho con el servicio.', false),
    ('Me llegó un cargo duplicado en mi tarjeta. Necesito que revisen la factura #12345 urgentemente.', false),
    ('Hola, quisiera saber si tienen planes empresariales y cuál es el proceso de onboarding.', false),
    ('Esto es inaceptable. Llevo 3 días sin poder acceder y nadie me responde. Voy a cancelar mi suscripción.', false),
    ('El botón de "Guardar" en la sección de configuración no responde. Probé en Chrome y Firefox.', false),
    ('Muchas gracias por la nueva funcionalidad de reportes. Es exactamente lo que necesitábamos.', false),
    ('No me queda claro cómo funciona el sistema de créditos. ¿Podrían explicarme?', false),
    ('ERROR: No se puede conectar al servidor. Código 500. Adjunto screenshot del error.', false),
    ('¿Cuándo estará disponible la integración con Salesforce que mencionaron en el último webinar?', false);

-- ============================================================================
-- FUNCIONES ESTADISTICAS
-- ============================================================================

-- Función para obtener estadísticas rápidas
CREATE OR REPLACE FUNCTION get_ticket_stats()
RETURNS TABLE(
    total_tickets BIGINT,
    processed_tickets BIGINT,
    pending_tickets BIGINT,
    avg_processing_time_ms NUMERIC,
    positivo_count BIGINT,
    neutral_count BIGINT,
    negativo_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_tickets,
        COUNT(*) FILTER (WHERE processed = true)::BIGINT as processed_tickets,
        COUNT(*) FILTER (WHERE processed = false)::BIGINT as pending_tickets,
        ROUND(AVG(processing_time_ms), 2) as avg_processing_time_ms,
        COUNT(*) FILTER (WHERE sentiment = 'Positivo')::BIGINT as positivo_count,
        COUNT(*) FILTER (WHERE sentiment = 'Neutral')::BIGINT as neutral_count,
        COUNT(*) FILTER (WHERE sentiment = 'Negativo')::BIGINT as negativo_count
    FROM tickets;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VERIFICACIÓN FINAL
-- ============================================================================

-- Verificar que todo se creó correctamente
DO $$
BEGIN
    RAISE NOTICE ' Schema creado exitosamente';
    RAISE NOTICE ' Tickets de prueba insertados: %', (SELECT COUNT(*) FROM tickets);
    RAISE NOTICE ' RLS habilitado: %', (SELECT relrowsecurity FROM pg_class WHERE relname = 'tickets');
END $$;