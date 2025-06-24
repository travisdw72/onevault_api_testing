// Customer Configuration Interfaces
export interface ILocation {
  id: string;
  name: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  timezone: string;
  isActive: boolean;
}

export interface IBrandingConfig {
  companyName: string;
  displayName: string;
  logo: {
    primary: string;
    secondary?: string;
    favicon: string;
  };
  colors: {
    primary: string;
    secondary: string;
    accent?: string;
    background: string;
    text: string;
  };
  fonts: {
    primary: string;
    secondary?: string;
  };
  customCss?: string;
}

export interface IComplianceConfig {
  requiredFrameworks: string[];
  hipaa: {
    enabled: boolean;
    baaRequired: boolean;
    auditRetentionYears: number;
    encryptionRequired: boolean;
  };
  gdpr: {
    enabled: boolean;
    dataRetentionDays: number;
    rightToBeForgitten: boolean;
    consentRequired: boolean;
  };
  sox: {
    enabled: boolean;
    financialReportingRequired: boolean;
    controlTestingRequired: boolean;
  };
  pciDss: {
    enabled: boolean;
    level: '1' | '2' | '3' | '4';
    merchantCategory: string;
  };
}

export interface ISecurityConfig {
  authentication: {
    mfaRequired: boolean;
    passwordPolicy: {
      minLength: number;
      requireUppercase: boolean;
      requireLowercase: boolean;
      requireNumbers: boolean;
      requireSpecialChars: boolean;
      maxAge: number;
    };
    sessionTimeout: number;
    maxFailedAttempts: number;
    lockoutDuration: number;
  };
  encryption: {
    algorithm: string;
    keyRotationDays: number;
    dataAtRest: boolean;
    dataInTransit: boolean;
  };
  audit: {
    logAllAccess: boolean;
    retentionDays: number;
    realTimeAlerts: boolean;
  };
}

export interface IPricingConfig {
  basePlan: {
    name: string;
    monthlyPrice: number;
    annualPrice: number;
    features: string[];
  };
  addOns: {
    id: string;
    name: string;
    monthlyPrice: number;
    annualPrice: number;
    description: string;
  }[];
  customization: {
    setupFee: number;
    hourlyRate: number;
    minimumHours: number;
  };
  billing: {
    currency: string;
    paymentTerms: string;
    invoiceFrequency: 'monthly' | 'quarterly' | 'annually';
  };
}

export interface ITenantConfig {
  id: string;
  name: string;
  domain: string;
  subdomain: string;
  isActive: boolean;
  users: {
    maxUsers: number;
    adminUsers: string[];
    roles: string[];
  };
  features: {
    enabled: string[];
    disabled: string[];
    beta: string[];
  };
}

export interface IAnalyticsConfig {
  googleAnalytics: {
    enabled: boolean;
    trackingId?: string;
    customDimensions?: Record<string, string>;
  };
  customerAnalytics: {
    enabled: boolean;
    trackUserBehavior: boolean;
    trackBusinessMetrics: boolean;
    retentionDays: number;
  };
  reporting: {
    automated: boolean;
    frequency: 'daily' | 'weekly' | 'monthly';
    recipients: string[];
  };
}

export interface IIntegrationConfig {
  api: {
    enabled: boolean;
    rateLimit: number;
    apiKeys: {
      production: string;
      staging: string;
    };
  };
  webhooks: {
    enabled: boolean;
    endpoints: {
      url: string;
      events: string[];
      secret: string;
    }[];
  };
  thirdParty: {
    [serviceName: string]: {
      enabled: boolean;
      apiKey?: string;
      configuration?: Record<string, any>;
    };
  };
}

export interface ICustomerConfig {
  // Core identification
  customerId: string;
  customerName: string;
  industryType: 'spa_wellness' | 'financial_services' | 'equestrian' | 'property_management' | 'healthcare' | 'professional_services';
  
  // Configuration sections
  branding: IBrandingConfig;
  locations: ILocation[];
  compliance: IComplianceConfig;
  security: ISecurityConfig;
  pricing: IPricingConfig;
  tenants: ITenantConfig[];
  analytics: IAnalyticsConfig;
  integrations: IIntegrationConfig;
  
  // Metadata
  createdDate: string;
  lastUpdated: string;
  configVersion: string;
  environment: 'development' | 'staging' | 'production';
  
  // Custom fields for industry-specific requirements
  customFields?: Record<string, any>;
} 