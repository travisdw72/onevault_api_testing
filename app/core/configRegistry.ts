import { ICustomerConfig } from '../interfaces/config/customerConfig.interface';
import { oneSpaConfig } from '../../../customers/configurations/one_spa/oneSpaConfig';
import { oneBarnConfig } from '../../../customers/configurations/one_barn/oneBarnConfig';

// Configuration Registry Interface
export interface IConfigRegistry {
  getCustomerConfig(customerId: string): ICustomerConfig | null;
  getAllCustomerIds(): string[];
  isValidCustomer(customerId: string): boolean;
  getCustomerByDomain(domain: string): ICustomerConfig | null;
  getActiveCustomers(): ICustomerConfig[];
  validateConfig(config: ICustomerConfig): IConfigValidationResult;
}

export interface IConfigValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// Configuration Registry Implementation
class ConfigRegistry implements IConfigRegistry {
  private readonly configs: Map<string, ICustomerConfig> = new Map();

  constructor() {
    this.loadConfigurations();
  }

  private loadConfigurations(): void {
    // Register all customer configurations
    this.registerConfig(oneSpaConfig);
    this.registerConfig(oneBarnConfig);
    
    // Future customer configs would be registered here:
    // this.registerConfig(financial_services_config);
    // this.registerConfig(property_management_config);
    
    console.log(`Loaded ${this.configs.size} customer configurations`);
  }

  private registerConfig(config: ICustomerConfig): void {
    const validation = this.validateConfig(config);
    
    if (!validation.isValid) {
      throw new Error(`Invalid configuration for ${config.customerId}: ${validation.errors.join(', ')}`);
    }

    if (validation.warnings.length > 0) {
      console.warn(`Configuration warnings for ${config.customerId}:`, validation.warnings);
    }

    this.configs.set(config.customerId, config);
    console.log(`Registered configuration for: ${config.customerName} (${config.customerId})`);
  }

  public getCustomerConfig(customerId: string): ICustomerConfig | null {
    return this.configs.get(customerId) || null;
  }

  public getAllCustomerIds(): string[] {
    return Array.from(this.configs.keys());
  }

  public isValidCustomer(customerId: string): boolean {
    return this.configs.has(customerId);
  }

  public getCustomerByDomain(domain: string): ICustomerConfig | null {
    for (const config of this.configs.values()) {
      // Check main branding domain
      if (config.branding && domain.includes(config.branding.companyName.toLowerCase().replace(/\s+/g, ''))) {
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
  }

  public getActiveCustomers(): ICustomerConfig[] {
    return Array.from(this.configs.values()).filter(config => 
      config.tenants.some(tenant => tenant.isActive)
    );
  }

  public validateConfig(config: ICustomerConfig): IConfigValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Required field validations
    if (!config.customerId) {
      errors.push('customerId is required');
    }

    if (!config.customerName) {
      errors.push('customerName is required');
    }

    if (!config.industryType) {
      errors.push('industryType is required');
    }

    // Branding validations
    if (!config.branding?.companyName) {
      errors.push('branding.companyName is required');
    }

    if (!config.branding?.colors?.primary) {
      errors.push('branding.colors.primary is required');
    }

    // Location validations
    if (!config.locations || config.locations.length === 0) {
      errors.push('At least one location is required');
    } else {
      config.locations.forEach((location, index) => {
        if (!location.id) {
          errors.push(`Location ${index} missing id`);
        }
        if (!location.name) {
          errors.push(`Location ${index} missing name`);
        }
        if (!location.address?.street) {
          errors.push(`Location ${index} missing address.street`);
        }
      });
    }

    // Tenant validations
    if (!config.tenants || config.tenants.length === 0) {
      errors.push('At least one tenant is required');
    } else {
      config.tenants.forEach((tenant, index) => {
        if (!tenant.id) {
          errors.push(`Tenant ${index} missing id`);
        }
        if (!tenant.domain) {
          errors.push(`Tenant ${index} missing domain`);
        }
      });
    }

    // Security validations
    if (config.security?.authentication?.passwordPolicy?.minLength < 8) {
      warnings.push('Password minimum length should be at least 8 characters');
    }

    if (!config.security?.authentication?.mfaRequired && config.compliance?.hipaa?.enabled) {
      warnings.push('MFA should be required for HIPAA compliance');
    }

    // Compliance validations
    if (config.compliance?.hipaa?.enabled && !config.security?.encryption?.dataAtRest) {
      errors.push('Data at rest encryption is required for HIPAA compliance');
    }

    if (config.compliance?.pciDss?.enabled && !config.security?.encryption?.dataInTransit) {
      errors.push('Data in transit encryption is required for PCI DSS compliance');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }
}

// Singleton instance
export const configRegistry = new ConfigRegistry();

// Helper functions following the established pattern
export const getCustomerConfig = (customerId: string): ICustomerConfig | null => {
  return configRegistry.getCustomerConfig(customerId);
};

export const getCustomerByDomain = (domain: string): ICustomerConfig | null => {
  return configRegistry.getCustomerByDomain(domain);
};

export const getAllCustomerIds = (): string[] => {
  return configRegistry.getAllCustomerIds();
};

export const isValidCustomer = (customerId: string): boolean => {
  return configRegistry.isValidCustomer(customerId);
};

export const getActiveCustomers = (): ICustomerConfig[] => {
  return configRegistry.getActiveCustomers();
};

export const validateCustomerConfig = (config: ICustomerConfig): IConfigValidationResult => {
  return configRegistry.validateConfig(config);
};

// Configuration utilities
export const getCustomerEnvironment = (customerId: string): string => {
  const config = getCustomerConfig(customerId);
  return config?.environment || 'development';
};

export const getCustomerComplianceFrameworks = (customerId: string): string[] => {
  const config = getCustomerConfig(customerId);
  if (!config) return [];

  return Object.entries(config.compliance)
    .filter(([key, value]) => 
      typeof value === 'object' && 
      value !== null && 
      'enabled' in value && 
      value.enabled
    )
    .map(([key]) => key.toUpperCase());
};

export const getCustomerBrandingVars = (customerId: string): Record<string, string> => {
  const config = getCustomerConfig(customerId);
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
};

export const getCustomerTenantBySubdomain = (customerId: string, subdomain: string): any => {
  const config = getCustomerConfig(customerId);
  if (!config) return null;

  return config.tenants.find(tenant => tenant.subdomain === subdomain);
};

export const getCustomerIntegrationConfig = (customerId: string, integrationName: string): any => {
  const config = getCustomerConfig(customerId);
  if (!config) return null;

  return config.integrations.thirdParty[integrationName] || null;
};

// Export for use in FastAPI backend
export default configRegistry; 