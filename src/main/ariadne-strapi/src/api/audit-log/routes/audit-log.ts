/**
 * $api router
 */

export default {
  routes: [
    {
      method: 'GET',
      path: '/audit-log',
      handler: 'audit-log.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/audit-log/:id',
      handler: 'audit-log.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/audit-log',
      handler: 'audit-log.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/audit-log/:id',
      handler: 'audit-log.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/audit-log/:id',
      handler: 'audit-log.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
