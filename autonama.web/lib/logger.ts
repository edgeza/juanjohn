// Simplified logger for web frontend
const createLogger = () => {
  const log = (level: string, message: string, meta: any = {}) => {
    const logEntry = {
      '@timestamp': new Date().toISOString(),
      level: level.toUpperCase(),
      message,
      service: 'autonama_web',
      environment: process.env.NODE_ENV || 'development',
      host: 'web-container',
      ...meta
    };
    
    console.log(JSON.stringify(logEntry));
  };

  return {
    info: (message: string, meta: any = {}) => log('info', message, meta),
    error: (message: string, meta: any = {}) => log('error', message, meta),
    warn: (message: string, meta: any = {}) => log('warn', message, meta),
    debug: (message: string, meta: any = {}) => log('debug', message, meta),
  };
};

const logger = createLogger();

// API logging helper
export const apiLogger = {
  info: (message: string, meta: any = {}) => {
    logger.info(message, { ...meta, component: 'api' });
  },
  
  error: (message: string, error?: Error, meta: any = {}) => {
    logger.error(message, {
      ...meta,
      component: 'api',
      error: error?.message,
      stack: error?.stack
    });
  },
  
  warn: (message: string, meta: any = {}) => {
    logger.warn(message, { ...meta, component: 'api' });
  }
};

// Component logging helper
export const componentLogger = {
  info: (component: string, message: string, meta: any = {}) => {
    logger.info(message, { ...meta, component, type: 'component' });
  },
  
  error: (component: string, message: string, error?: Error, meta: any = {}) => {
    logger.error(message, {
      ...meta,
      component,
      type: 'component',
      error: error?.message,
      stack: error?.stack
    });
  }
};

export default logger;
