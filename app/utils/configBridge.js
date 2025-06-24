#!/usr/bin/env node

/**
 * Bridge to execute TypeScript configuration functions from Python
 * Usage: node configBridge.js <function_name> [arguments...]
 */

const fs = require('fs');
const path = require('path');

// Mock TypeScript config for testing (until we have proper TS compilation)
const mockCustomerConfigs = {
  'ONE_SPA_LUXE_WELLNESS': {
    customerId: 'ONE_SPA_LUXE_WELLNESS',
    customerName: 'Luxe Wellness Spa Collection',
    industryType: 'spa_wellness',
    branding: {
      companyName: 'Luxe Wellness Spa Collection',
      displayName: 'The ONE Spa',
      colors: {
        primary: '#2D5AA0',
        secondary: '#E8B931',
        accent: '#F5F5F5',
        background: '#FFFFFF',
        text: '#2C3E50'
      },
      fonts: {
        primary: 'Montserrat, sans-serif',
        secondary: 'Playfair Display, serif'
      }
    },
    locations: [
      {
        id: 'BEVERLY_HILLS',
        name: 'Beverly Hills Flagship',
        isActive: true
      },
      {
        id: 'MANHATTAN_BEACH',
        name: 'Manhattan Beach Oceanside',
        isActive: true
      },
      {
        id: 'NEWPORT_BEACH',
        name: 'Newport Beach Harbor',
        isActive: true
      }
    ],
    compliance: {
      requiredFrameworks: ['HIPAA', 'CCPA', 'PCI_DSS'],
      hipaa: {
        enabled: true,
        baaRequired: true,
        auditRetentionYears: 6,
        encryptionRequired: true
      },
      gdpr: {
        enabled: false,
        dataRetentionDays: 0,
        rightToBeForgitten: false,
        consentRequired: false
      },
      sox: {
        enabled: false,
        financialReportingRequired: false,
        controlTestingRequired: false
      },
      pciDss: {
        enabled: true,
        level: '4',
        merchantCategory: 'spa_wellness_services'
      }
    },
    security: {
      authentication: {
        mfaRequired: true,
        passwordPolicy: {
          minLength: 12,
          requireUppercase: true,
          requireLowercase: true,
          requireNumbers: true,
          requireSpecialChars: true,
          maxAge: 90
        },
        sessionTimeout: 30,
        maxFailedAttempts: 3,
        lockoutDuration: 15
      },
      encryption: {
        algorithm: 'AES-256-GCM',
        keyRotationDays: 90,
        dataAtRest: true,
        dataInTransit: true
      },
      audit: {
        logAllAccess: true,
        retentionDays: 2555,
        realTimeAlerts: true
      }
    },
    tenants: [
      {
        id: 'CORPORATE',
        name: 'Corporate Management',
        domain: 'corporate.luxewellness.com',
        subdomain: 'corporate',
        isActive: true
      },
      {
        id: 'BEVERLY_HILLS',
        name: 'Beverly Hills Location',
        domain: 'beverlyhills.luxewellness.com',
        subdomain: 'beverlyhills',
        isActive: true
      }
    ],
    environment: 'production',
    createdDate: '2024-01-15T08:00:00Z',
    lastUpdated: '2024-12-20T10:30:00Z',
    configVersion: '2.1.0'
  }
};

// Configuration functions matching TypeScript interface
const configFunctions = {
  getCustomerConfig: (customerId) => {
    return mockCustomerConfigs[customerId] || null;
  },

  getAllCustomerIds: () => {
    return Object.keys(mockCustomerConfigs);
  },

  isValidCustomer: (customerId) => {
    return customerId in mockCustomerConfigs;
  },

  getCustomerByDomain: (domain) => {
    for (const config of Object.values(mockCustomerConfigs)) {
      // Check branding domain
      if (domain.includes(config.branding.companyName.toLowerCase().replace(/\s+/g, ''))) {
        return config;
      }
      
      // Check tenant domains
      for (const tenant of config.tenants) {
        if (tenant.domain === domain || domain.includes(tenant.subdomain)) {
          return config;
        }
      }
    }
    return null;
  },

  getActiveCustomers: () => {
    return Object.values(mockCustomerConfigs).filter(config => 
      config.tenants.some(tenant => tenant.isActive)
    );
  },

  getCustomerComplianceFrameworks: (customerId) => {
    const config = configFunctions.getCustomerConfig(customerId);
    if (!config) return [];

    return Object.entries(config.compliance)
      .filter(([key, value]) => 
        typeof value === 'object' && 
        value !== null && 
        'enabled' in value && 
        value.enabled
      )
      .map(([key]) => key.toUpperCase());
  },

  getCustomerBrandingVars: (customerId) => {
    const config = configFunctions.getCustomerConfig(customerId);
    if (!config?.branding) return {};

    const { colors, fonts } = config.branding;
    return {
      '--primary-color': colors.primary,
      '--secondary-color': colors.secondary,
      '--accent-color': colors.accent || '#F5F5F5',
      '--background-color': colors.background,
      '--text-color': colors.text,
      '--primary-font': fonts.primary,
      '--secondary-font': fonts.secondary || fonts.primary,
    };
  },

  getCustomerTenantBySubdomain: (customerId, subdomain) => {
    const config = configFunctions.getCustomerConfig(customerId);
    if (!config) return null;

    return config.tenants.find(tenant => tenant.subdomain === subdomain) || null;
  },

  getCustomerIntegrationConfig: (customerId, integrationName) => {
    const config = configFunctions.getCustomerConfig(customerId);
    if (!config || !config.integrations) return null;

    return config.integrations.thirdParty?.[integrationName] || null;
  },

  getCustomerEnvironment: (customerId) => {
    const config = configFunctions.getCustomerConfig(customerId);
    return config?.environment || 'development';
  }
};

// Parse command line arguments
const args = process.argv.slice(2);

if (args.length === 0) {
  console.error('Usage: node configBridge.js <function_name> [arguments...]');
  process.exit(1);
}

const functionName = args[0];
const functionArgs = args.slice(1);

// Execute the requested function
try {
  if (!(functionName in configFunctions)) {
    throw new Error(`Function '${functionName}' not found`);
  }

  const result = configFunctions[functionName](...functionArgs);
  console.log(JSON.stringify(result, null, 0));
} catch (error) {
  console.error(`Error executing ${functionName}:`, error.message);
  process.exit(1);
} 