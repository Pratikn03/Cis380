"use client";

import {
  ApolloClient,
  ApolloLink,
  ApolloProvider,
  HttpLink,
  InMemoryCache,
  split,
} from "@apollo/client";
import { GraphQLWsLink } from "@apollo/client/link/subscriptions";
import { getMainDefinition } from "@apollo/client/utilities";
import { createClient } from "graphql-ws";
import { useMemo } from "react";
import { getAuthToken } from "@/lib/auth";

function buildClient() {
  const base = process.env.NEXT_PUBLIC_GRAPHQL_HTTP ?? "http://localhost:8081/graphql";
  const wsBase = process.env.NEXT_PUBLIC_GRAPHQL_WS ?? "ws://localhost:8081/graphql";

  const httpLink = new HttpLink({
    uri: base,
    fetch,
  });

  const authLink = new ApolloLink((operation, forward) => {
    const token = getAuthToken();
    operation.setContext(({ headers = {} }) => ({
      headers: {
        ...headers,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }));
    return forward(operation);
  });

  const browserWsLink =
    typeof window !== "undefined"
      ? new GraphQLWsLink(
          createClient({
            url: wsBase,
            connectionParams: () => {
              const token = getAuthToken();
              return token ? { Authorization: `Bearer ${token}` } : {};
            },
          }),
        )
      : null;

  const link =
    browserWsLink == null
      ? authLink.concat(httpLink)
      : split(
          ({ query }) => {
            const definition = getMainDefinition(query);
            return (
              definition.kind === "OperationDefinition" && definition.operation === "subscription"
            );
          },
          browserWsLink,
          authLink.concat(httpLink),
        );

  return new ApolloClient({
    link,
    cache: new InMemoryCache(),
    devtools: {
      enabled: process.env.NODE_ENV !== "production",
    },
  });
}

export default function GraphQLProvider({ children }: { children: React.ReactNode }) {
  const client = useMemo(() => buildClient(), []);
  return <ApolloProvider client={client}>{children}</ApolloProvider>;
}
